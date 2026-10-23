"""Bind each F3a overview iteration's exact public Android source, result and APK contracts."""
import argparse,hashlib,json,subprocess,zipfile,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);parser.add_argument('--expected-host-methods',required=True,type=int);parser.add_argument('--expected-inputs',required=True,type=int);args=parser.parse_args()
build=M4/args.build;assert build.parent==M4
target=HERE/(args.build+'-capture.json');assert not target.exists()
result=read(build/'build-result.json');sources=read(build/'source-at-build-start.json')['files'];assert len(sources)==args.expected_inputs
prior=read(M4/'asset-import-gate-0001/gate.json')['android_source_sha256']
delta={name:value for name,value in sources.items() if prior.get(name)!=value}
for name,value in sources.items():assert sha(ROOT/name)==value,name
for name,value in delta.items():
    p=HERE/(args.build+'-tested-sources')/name;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists()
    p.write_bytes((ROOT/name).read_bytes());assert sha(p)==value
suites=[ET.parse(p).getroot() for p in (build/'host-tests').rglob('TEST-*.xml')]
totals={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ['tests','failures','errors','skipped']}
record=dict(status='FAILED_ITERATION_PRESERVED_NOT_HOST_OR_DEVICE_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    build=args.build,variant=result['variant'],android_inputs=len(sources),host_xml_totals=totals,tested_source_sha256=delta,
    build_result_sha256=sha(build/'build-result.json'),gradle_log_sha256=sha(build/'gradle.log'),commands=[])
if result['exit_code']==0:
    assert totals==dict(tests=args.expected_host_methods,failures=0,errors=0,skipped=0)
    record['apk_sha256']={p.name:sha(p) for p in build.glob('*.apk')}
    product=build/('app-'+result['variant']+'.apk');test=build/('app-'+result['variant']+'-androidTest.apk')
    aapt=ROOT/'vendor/android-sdk/build-tools/37.0.0/aapt2.exe'
    for apk in [product,test]:
        for command in [['dump','permissions',str(apk)],['dump','xmltree',str(apk),'--file','AndroidManifest.xml']]:
            argv=[str(aapt),*command];out=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',errors='replace',check=True,timeout=30)
            record['commands'].append(dict(argv=argv,returncode=out.returncode,stdout=out.stdout,stderr=out.stderr))
            if apk==product:assert 'android.permission.INTERNET' not in out.stdout and 'AssetFixtureProvider' not in out.stdout and 'AssetFixtureGrantReceiver' not in out.stdout
            if apk==test and command[1]=='xmltree':
                assert 'AssetFixtureProvider' in out.stdout and 'AssetFixtureGrantReceiver' in out.stdout and 'android.permission.DUMP' in out.stdout
        with zipfile.ZipFile(apk) as archive:
            assert archive.testzip() is None
            if apk==product:
                assert hashlib.sha256(archive.read('assets/release-trust.json')).hexdigest()=='2bf01e87216790babca17fd0990731cf57a3877430a9662642a0f5e0d99c87a5'
                native=archive.read('lib/arm64-v8a/libpackrag_jni.so');assert len(native)==5597496
                assert hashlib.sha256(native).hexdigest()=='361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef'
            else:
                fixture=archive.read('assets/asset-import-source/template-valid.jinja');assert len(fixture)==5443
                assert hashlib.sha256(fixture).hexdigest()=='ea663864491de7ade391839479860ca95541f892f72665c73251fbd4643b1bef'
    record['status']='PASS_LOCAL_F3F4_BUILD_HOST_APK_CONTRACTS_NOT_DEVICE_OR_INCREMENT_ACCEPTANCE'
    record['scope']='Explicit independently specified host/input counts, exact XML totals/source bytes, native/trust/permissions and public APK contracts. Gradle logs distinguish executed versus unchanged UP-TO-DATE tasks. No physical/security/UI/milestone or final release acceptance inferred. Prior F3a artifacts stay dated; final combined suite must use the actual final sources.'
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'],len(delta),'source deltas',flush=True)
