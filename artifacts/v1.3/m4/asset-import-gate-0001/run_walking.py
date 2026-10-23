"""Fresh F2 API walking attempt. Install, narrow grant, actual test, originals, guards."""
import argparse,hashlib,json,re,subprocess,traceback
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
ADB=ROOT/'vendor/platform-tools/adb.exe';SERIAL='R3CT908DHHR'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);parser.add_argument('--run',required=True);args=parser.parse_args()
build=M4/args.build;run=M4/args.run;assert build.parent==M4 and run.parent==M4 and not run.exists()
host=read(HERE/(args.build+'-capture.json'));assert host['status']=='PASS_F2_API_ITERATION_HOST_APK_CONTRACTS_NOT_DEVICE_OR_F2_ACCEPTANCE'
variant=host['variant'];sources=read(build/'source-at-build-start.json')['files']
for name,value in sources.items():assert sha(ROOT/name)==value,name
for name,value in host['apk_sha256'].items():assert sha(build/name)==value,name
expected=read(HERE/'before.json')['owner_public_file_sha256'];assert len(expected)==50
assert all(re.fullmatch(r'[A-Za-z0-9_.@/-]+',name) and '.private' not in Path(name).parts for name in expected)
run.mkdir();manifest=run/'instrumentation-manifest.json';execution=run/'execution.json'
record=dict(status='RUNNING',started_at=datetime.now(timezone.utc).isoformat(),serial=SERIAL,variant=variant,
    build=args.build,runner_sha256=sha(Path(__file__)),class_name='org.packrag.product.LocalAssetImportWalkingDeviceTest',
    selected_test_sources={'org.packrag.product.LocalAssetImportWalkingDeviceTest':dict(source='product/android/app/src/androidTest/java/org/packrag/product/LocalAssetImportWalkingDeviceTest.kt',source_sha256=sources['product/android/app/src/androidTest/java/org/packrag/product/LocalAssetImportWalkingDeviceTest.kt'])},
    apk_sha256=host['apk_sha256'],host_capture_sha256=sha(HERE/(args.build+'-capture.json')),commands=[])
def save():
    manifest.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
def command(argv,timeout=60):
    start=datetime.now(timezone.utc).isoformat();out=subprocess.run(argv,capture_output=True,timeout=timeout)
    record['commands'].append(dict(argv=argv,started_at=start,ended_at=datetime.now(timezone.utc).isoformat(),returncode=out.returncode,
        stdout=out.stdout.decode('utf-8',errors='replace'),stderr=out.stderr.decode('utf-8',errors='replace')));save()
    assert out.returncode==0,(argv,out.returncode);return out
def guard(label):
    out=command([str(ADB),'-s',SERIAL,'shell','run-as','org.packrag.product','sha256sum',*['files/'+name for name in sorted(expected)]])
    found={}
    for line in out.stdout.decode('utf-8').splitlines():
        value,name=line.split(maxsplit=1);assert re.fullmatch('[0-9a-f]{64}',value) and name.startswith('files/');found[name[6:]]=value
    record[label]=found;save();assert found==expected,label
try:
    guard('owner_known50_before')
    for name in ['app-'+variant+'.apk','app-'+variant+'-androidTest.apk']:
        out=command([str(ADB),'-s',SERIAL,'install','-r',str(build/name)],180);assert b'Success' in out.stdout
    out=command([str(ADB),'-s',SERIAL,'shell','am','broadcast','--user','0','-n','org.packrag.product.test/org.packrag.product.AssetFixtureGrantReceiver',
        '-a','org.packrag.product.test.GRANT_TEMPLATE']);assert b'result=1' in out.stdout and b'NARROW_TEMPLATE_READ_GRANTED' in out.stdout
    print(args.run,'actual narrow template read grant PASS; native walking test START',flush=True)
    out=command([str(ADB),'-s',SERIAL,'shell','am','instrument','-w','-r','-e','class',record['class_name'],
        'org.packrag.product.test/androidx.test.runner.AndroidJUnitRunner'],1200)
    (run/'instrumentation.txt').write_bytes(out.stdout+out.stderr)
    assert b'OK (1 test)' in out.stdout and b'FAILURES' not in out.stdout,'Actual instrumentation failed; later F2 progression held'
    out=command([str(ADB),'-s',SERIAL,'shell','run-as','org.packrag.product','cat','files/m4-local-asset-import-walking.json'],30)
    raw=run/'original-adb';raw.mkdir();(raw/'m4-local-asset-import-walking.json').write_bytes(out.stdout)
    device=json.loads(out.stdout);(run/'m4-local-asset-import-walking.json').write_text(json.dumps(device,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    record['saved_original_sha256']=sha(raw/'m4-local-asset-import-walking.json');save()
    assert device['status']=='PASS' and device['variant']==variant
    ids=['actual-narrow-read-grant-to-separate-provider-uid','actual-pinned-pre-import-native-walking-answer',
        'actual-foreign-native-reader-rejects-import-before-provider-open-or-replacement',
        'actual-template-stream-private-readback-atomic-replacement-and-caller-native-release','observed-bytes-and-commit-progress-contract',
        'one-actual-provider-descriptor-open-and-close-without-error','actual-post-import-cold-native-retrieval-admission-selection-citation-answer']
    assert [case['id'] for case in device['cases']]==ids and all(case['passed'] is True for case in device['cases'])
    assert device['owner_registry_and_model_sha256']==expected and device['guards_unchanged'] is True
    assert device['actual_weight_inference'] is True and device['raw_reasoning_persisted'] is False
    assert device['provider_before']['provider_uid']==device['provider_after']['provider_uid']!=device['product_uid']
    assert device['provider_after']['opens']==device['provider_before']['opens']+1
    assert device['provider_after']['closes']==device['provider_before']['closes']+1
    assert device['provider_after']['close_errors']==device['provider_before']['close_errors']
    assert device['import_bytes']==5443 and device['import_sha256']=='ea663864491de7ade391839479860ca95541f892f72665c73251fbd4643b1bef'
    assert datetime.fromisoformat(device['completed_at'].replace('Z','+00:00'))>datetime.fromisoformat(record['started_at'])
    assert device['directory_synced'] is True
    for side in ['before','after']:
        assert '74 °C' in device['answer_'+side] and '[S1]' in device['answer_'+side]
        assert device['initialization_ms_'+side]>0 and 1<=device['emitted_tokens_'+side]<=512
    guard('owner_known50_after')
    record.update(status='PASS',finished_at=datetime.now(timezone.utc).isoformat(),case_ids=ids,
        acceptance='F2_API_TEMPLATE_WALKING_ITERATION_ONLY_NOT_SYSTEM_PICKER_FULL_F2_M4_OR_PRODUCT',
        scope='Real separate-UID test provider, shell/DUMP-protected explicit narrow grant. No adopted product permissions or radio changes. Existing owner50 public paths unchanged; no claim of new full directory enumeration. Two actual cold answers and fixed pinned template replacement in independent copied-model root. Functional timings are not M8 performance acceptance. All-slot, cancellation/restart/fault, UI/policy/adjacent/closure/checkpoint still pending.')
except Exception as failure:
    record.update(status='FAIL',finished_at=datetime.now(timezone.utc).isoformat(),failure_type=type(failure).__name__,failure_message=str(failure))
    (run/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
finally:
    save();execution.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(record['acceptance'],flush=True)
