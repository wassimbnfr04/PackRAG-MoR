"""E2 current source/host/history/APK audit; explicit single-build or matched-pair scope."""
import argparse,hashlib,json,subprocess,zipfile,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(values):
    for name,value in values.items():assert digest(ROOT/name)==value,name
def audit(build,variant,prefix):
    folder=M4/build;assert read(folder/'build-result.json')['exit_code']==0
    files=read(folder/'source-at-build-start.json')['files'];check(files)
    suites=[ET.parse(p).getroot() for p in (folder/'host-tests').rglob('TEST-*.xml')]
    totals={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ['tests','failures','errors','skipped']}
    assert totals==dict(tests=40,failures=0,errors=0,skipped=0),totals
    apk=folder/f'app-{variant}.apk';commands=[]
    for mode in ['permissions','badging']:
        args=[str(ROOT/'vendor/android-sdk/build-tools/37.0.0/aapt2.exe'),'dump',mode,str(apk)]
        result=subprocess.run(args,capture_output=True,check=True);p=HERE/f'{prefix}-{mode}.txt';assert not p.exists();p.write_bytes(result.stdout+result.stderr)
        commands.append(dict(argv=args,returncode=result.returncode))
    assert 'android.permission.INTERNET' not in (HERE/f'{prefix}-permissions.txt').read_text()
    assert 'application-debuggable' in (HERE/f'{prefix}-badging.txt').read_text()
    with zipfile.ZipFile(apk) as archive:
        entries=archive.namelist();p=HERE/f'{prefix}-apk-entries.txt';assert not p.exists();p.write_text('\n'.join(sorted(entries))+'\n')
        assert not any(Path(e).suffix.lower() in {'.jks','.key','.keystore','.pem','.seed','.seed32'} for e in entries)
        assert not any(e.startswith('assets/'+n+'/') for e in entries for n in ['source-details-corpus','representation-corpus','source-text-corpus','selection-corpus','conflict-corpus'])
        store=hashlib.sha256(archive.read('assets/release-trust.json')).hexdigest();assert store==digest(ROOT/'product/config/release-trust.json')=='2bf01e87216790babca17fd0990731cf57a3877430a9662642a0f5e0d99c87a5'
        native=hashlib.sha256(archive.read('lib/arm64-v8a/libpackrag_jni.so')).hexdigest();assert native=='361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef'
        if variant=='demo':assert not {'assets/development-public-key.raw','assets/lifecycle-public-key.raw','assets/developer-public-key.raw'}.intersection(entries)
    with zipfile.ZipFile(folder/f'app-{variant}-androidTest.apk') as archive:
        asset=ROOT/'product/android/app/src/androidTest/assets/source-details-corpus'
        for p in asset.iterdir():assert hashlib.sha256(archive.read('assets/source-details-corpus/'+p.name)).hexdigest()==digest(p)
    return dict(build=build,variant=variant,hosts=totals,source_sha256=files,
        apk_sha256={p.name:digest(p) for p in folder.glob('*.apk')},no_internet=True,public_store_sha256=store,native_sha256=native,commands=commands)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pair',action='store_true');args=parser.parse_args()
    prefix='repaired-pair' if args.pair else 'repaired-debug';target=HERE/f'{prefix}-preflight.json';assert not target.exists()
    old=read(M4/'ui-query-gate-0002/gate.json');check(old['output_sha256'])
    history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];check(history)
    python=read(M4/'run-0015/result-manifest.json');assert python['status']=='PASS' and python['totals']==dict(tests=1034,failures=0,errors=0,skipped=0)
    sources={n:v for n,v in python['source_sha256'].items() if n not in ['PLAN.md','STATUS.md','DECISIONS.md']};check(sources)
    debug=audit('build-0041','debug',prefix+'-debug');builds=[debug]
    if args.pair:
        policy=audit('build-0042','demo',prefix+'-policy');assert policy['source_sha256']==debug['source_sha256'];builds.append(policy)
    before=old['android_source_sha256'];current=debug['source_sha256'];assert set(before).issubset(current)
    changes={name:value for name,value in current.items() if before.get(name)!=value}
    target.write_text(json.dumps(dict(status='PASS_E2_SOURCE_HOST_HISTORY_AND_PACKAGED_APK_NOT_DEVICE_OR_CLOSURE',
        recorded_utc=datetime.now(timezone.utc).isoformat(),matched_variants=args.pair,builds=builds,android_inputs=len(current),changed_android_inputs=changes,
        runtime_inputs=len(sources),source_sha256=sources,prior_e1_public_outputs_unchanged=len(old['output_sha256']),historical_unchanged=len(history),
        limits='Both builds are debug signed/instrumentable. Filename checks are bounded checks, not exhaustive secret scanning. Physical/UI/all retained gates and E2 closure still required.'),indent=2)+'\n',encoding='utf-8')
    print('E2_'+prefix.upper()+'_PREFLIGHT_PASS_NOT_MILESTONE_CLOSURE')
if __name__=='__main__':main()
