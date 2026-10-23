"""Final E1 input/host/history and packaged-policy audit; no private custody access."""
import hashlib,json,subprocess,zipfile,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
target=HERE/'preflight-repaired.json';assert not target.exists()
debug=read(M4/'build-0035/source-at-build-start.json')['files'];policy=read(M4/'build-0036/source-at-build-start.json')['files'];assert debug==policy
for name,value in debug.items():assert digest(ROOT/name)==value,name
old=read(M4/'selection-gate-0002/gate.json');changes={name:value for name,value in debug.items() if old['android_source_sha256'].get(name)!=value}
expected={
    'product/android/app/src/main/java/org/packrag/product/'+name for name in ['MainActivity.kt','PackRagViewModel.kt','QueryPresentation.kt']
}|{'product/android/app/src/androidTest/java/org/packrag/product/'+name for name in ['PackManagementUiTest.kt','QueryControlsDeviceTest.kt','QueryControlsUiTest.kt','QueryControlsPolicyTest.kt']}
expected.add('product/android/app/src/test/java/org/packrag/product/QueryPresentationTest.kt')
assert set(changes)==expected,(changes,expected);assert set(old['android_source_sha256']).issubset(debug)
for name,value in old['source_sha256'].items():assert digest(ROOT/name)==value,name
for name,value in old['output_sha256'].items():assert digest(ROOT/name)==value,name
history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files']
for name,value in history.items():assert digest(ROOT/name)==value,name
hosts={}
for build in ['build-0035','build-0036']:
    assert read(M4/build/'build-result.json')['exit_code']==0
    suites=[ET.parse(p).getroot() for p in (M4/build/'host-tests').rglob('TEST-*.xml')]
    totals={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ['tests','failures','errors','skipped']}
    assert totals==dict(tests=37,failures=0,errors=0,skipped=0),totals;hosts[build]=totals
apk=M4/'build-0036/app-demo.apk';commands=[]
for mode in ['permissions','badging']:
    args=[str(ROOT/'vendor/android-sdk/build-tools/37.0.0/aapt2.exe'),'dump',mode,str(apk)]
    result=subprocess.run(args,capture_output=True,check=True);(HERE/('repaired-'+mode+'.txt')).write_bytes(result.stdout+result.stderr)
    commands.append(dict(argv=args,returncode=result.returncode))
assert 'android.permission.INTERNET' not in (HERE/'repaired-permissions.txt').read_text()
assert 'application-debuggable' in (HERE/'repaired-badging.txt').read_text()
private={'.jks','.key','.keystore','.pem','.seed'}
known=['assets/development-public-key.raw','assets/lifecycle-public-key.raw','assets/developer-public-key.raw']
namespaces=['conflict-corpus','prompt-v13-xml-corpus','relevance-corpus','relevance-reference-corpus','representation-corpus','source-text-corpus','selection-corpus']
with zipfile.ZipFile(apk) as archive:
    entries=sorted(archive.namelist());(HERE/'repaired-policy-apk-entries.txt').write_text('\n'.join(entries)+'\n')
    assert not set(known).intersection(entries)
    assert not any(Path(e).suffix.lower() in private for e in entries)
    assert not any(e.startswith('assets/'+n+'/') for e in entries for n in namespaces)
    store=archive.read('assets/release-trust.json');(HERE/'repaired-packaged-release-trust.json').write_bytes(store)
    store_hash=hashlib.sha256(store).hexdigest();assert store_hash==digest(ROOT/'product/config/release-trust.json')
    native_hash=hashlib.sha256(archive.read('lib/arm64-v8a/libpackrag_jni.so')).hexdigest()
    assert native_hash=='361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef'
record=dict(status='PASS_FINAL_SOURCE_HOST_HISTORY_AND_PACKAGED_POLICY_NOT_DEVICE_OR_E1_CLOSURE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    android_inputs=len(debug),changed_android_inputs=changes,runtime_inputs_unchanged=len(old['source_sha256']),d3_outputs_unchanged=len(old['output_sha256']),historical_unchanged=len(history),
    hosts=hosts,policy_apk_sha256=digest(apk),no_internet=True,approved_store_sha256=store_hash,native_sha256=native_hash,
    private_extension_name_checks=sorted(private),commands=commands,
    limits='Demo is instrumentable/debug signed, not final release; name checks are not exhaustive secret scanning; E1 physical/UI/retained gates and closure still required')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:record[k] for k in ['status','android_inputs','hosts','historical_unchanged']}))
