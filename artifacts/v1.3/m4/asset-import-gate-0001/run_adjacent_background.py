"""Fresh adjacent physical regressions; stop and preserve before any later class on failure."""
import argparse,hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4';ADB=ROOT/'vendor/platform-tools/adb.exe'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);parser.add_argument('--variant',choices=['debug','demo'],required=True);parser.add_argument('--prefix',required=True);parser.add_argument('--installed-proof',required=True);args=parser.parse_args()
target=HERE/(args.prefix+'-execution.json');assert target.parent==HERE and not target.exists()
proof=HERE/args.installed_proof;assert proof.parent==HERE and read(proof)['status']=='PASS_SERIAL_INSTALLED_EXACT_APK_PAIR_NO_TEST_ACCEPTANCE'
assert read(proof)['build']==args.build and read(proof)['variant']==args.variant
pair=read(HERE/'adjacent-source-pair-0001.json');assert pair['status']=='PASS_MATCHED_599_HOST73_GUARD_ONLY_BUILDS_NOT_PHONE_ACCEPTANCE'
build=M4/args.build;assert build.parent==M4 and pair['builds'][args.build]['variant']==args.variant
sources=read(build/'source-at-build-start.json')['files'];assert sources==pair['android_source_sha256']
def unchanged():
    for name,value in sources.items():assert sha(ROOT/name)==value,name
unchanged();baseline=read(HERE/'before.json')['owner_public_file_sha256']
readiness=('readiness','LocalAssetReadinessDeviceTest',3,{'m4-local-assets-negative.json':5,'m4-local-assets-runtime.json':5,'m4-local-assets-viewmodel.json':3})
plans={'debug':[readiness,
    ('query','QueryControlsDeviceTest',2,{'m4-ui-query-inputs.json':7,'m4-ui-query-runtime.json':4}),
    ('sources','SourceDetailsViewModelTest',1,{'m4-source-details-viewmodel.json':5}),
    ('diagnostics','DiagnosticRuntimeDeviceTest',1,{'m4-diagnostic-runtime.json':8}),
    ('lifecycle','DiagnosticLifecycleDeviceTest',1,{'m4-diagnostic-lifecycle.json':7})],
    'demo':[readiness,
    ('query-policy','QueryControlsPolicyTest',1,{'m4-ui-query-policy.json':3}),
    ('source-policy','SourceDetailsPolicyTest',1,{'m4-source-details-policy.json':2}),
    ('diagnostic-policy','DiagnosticPolicyDeviceTest',1,{'m4-diagnostic-policy.json':8})]}
plan=plans[args.variant]
for suffix,_,_,_ in plan:assert not (M4/(args.prefix+'-'+suffix)).exists()
record=dict(status='RUNNING_F2_ADJACENT_BACKGROUND_NOT_ACCEPTED',started_utc=datetime.now(timezone.utc).isoformat(),runner_sha256=sha(Path(__file__)),build=args.build,variant=args.variant,installed_proof_sha256=sha(proof),pair_sha256=sha(HERE/'adjacent-source-pair-0001.json'),plan=plan,commands=[],completed=[])
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
current_run=None;current_files=[]
def command(argv,label):
    print(args.prefix,label,'START',flush=True)
    with (HERE/(args.prefix+'-'+label+'.stdout.txt')).open('xb') as out,(HERE/(args.prefix+'-'+label+'.stderr.txt')).open('xb') as err:
        result=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=err)
    record['commands'].append(dict(argv=argv,returncode=result.returncode,label=label))
    target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'Hold F2/F3; preserve failed stage before proceeding'
    print(args.prefix,label,'PASS',flush=True)
def validate_report(value,count):
    assert value['status']=='PASS' and len(value['cases'])==count
    assert all(case['passed'] is True for case in value['cases'])
    assert len({case['id'] for case in value['cases']})==count
    if 'variant' in value:assert value['variant']==args.variant
    if 'owner_registry_and_model_sha256' in value:
        assert value['owner_registry_and_model_sha256']==baseline
        assert value['owner_guard_scope']=='EXPLICIT_50_PUBLIC_BASELINE_FILES_NO_ENUMERATION'
    if 'guards_unchanged' in value:assert value['guards_unchanged'] is True
    if 'compiled_developer_mode' in value:assert value['compiled_developer_mode'] is False
    if 'raw_reasoning_persisted' in value:assert value['raw_reasoning_persisted'] is False
    for name in ['answer','recovery_answer']:
        if name in value:
            assert '74 °C' in value[name] and '[S1]' in value[name] and '</think>' not in value[name]
    for name in ['cold','warm']:
        if name in value:
            data=value[name];assert data['outcome']=='ANSWER_ACCEPTED'
            assert '74 °C' in data['answer'] and '[S1]' in data['answer'] and '</think>' not in data['answer']
    if 'canonical_sha256' in value:assert value['canonical_sha256']=='266af80f5d4da1dac500acd9a2bcc1fd2317b2caf49141ebb586280b9df49333'
try:
    command([sys.executable,'-X','utf8',str(HERE/'capture_known_guard.py'),'--output',args.prefix+'-before-known.json'],'before-known')
    for suffix,class_name,methods,files in plan:
        unchanged();current_run=M4/(args.prefix+'-'+suffix);current_files=list(files)
        record['active_class']=class_name;target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        command([sys.executable,'-X','utf8',str(HERE/'test_android_installed_0001.py'),'--serial','R3CT908DHHR','--build',str(build),'--run',str(current_run),'--class-name','org.packrag.product.'+class_name,'--result-file',current_files[0],'--timeout','3000','--variant',args.variant],suffix+'-instrumentation')
        command([sys.executable,'-X','utf8','-m','scripts.v13_collect_phone_results','--run',str(current_run),'--files',','.join(current_files)],suffix+'-collect')
        manifest=read(current_run/'instrumentation-manifest.json');assert manifest['status']=='PASS' and manifest['variant']==args.variant
        junit=(current_run/'instrumentation.txt').read_text();assert re.search(r'OK \('+str(methods)+r' tests?\)',junit)
        assert manifest['transport']=='VERIFY_EXACT_INSTALLED_APKS_NO_REINSTALL'
        assert manifest['selected_test_sources']['org.packrag.product.'+class_name]['source_sha256']==sources['product/android/app/src/androidTest/java/org/packrag/product/'+class_name+'.kt']
        collection=read(current_run/'collected-results.json');assert set(collection['saved_sha256'])==set(files)
        for name,count in files.items():
            path=current_run/'original-adb'/name;assert sha(path)==collection['saved_sha256'][name]
            validate_report(read(path),count)
        unchanged();record['completed'].append(dict(class_name=class_name,methods=methods,controls=sum(files.values()),run=current_run.name,original_sha256=collection['saved_sha256'],manifest_sha256=sha(current_run/'instrumentation-manifest.json')))
        target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print('ACCEPTED_ORIGINALS',class_name,methods,sum(files.values()),flush=True)
    command([sys.executable,'-X','utf8',str(HERE/'capture_known_guard.py'),'--output',args.prefix+'-after-known.json'],'after-known')
    command([sys.executable,'-X','utf8',str(HERE/'prepare_full_sources.py'),'--build',args.build,'--output',args.prefix+'-after-source.json','--verify-only'],'after-source')
    unchanged();record.update(status='PASS_F2_FRESH_ADJACENT_BACKGROUND_VARIANT_NOT_FULL_F2',
        scope='Fresh per-class JUnit and exact original reports collected/validated before next class; fixed method/control counts; real pinned LFM accepted synthetic answers where specified. Actual exact installed APK hashes checked before every class, no repeated installs. Only explicit50 public owner files guarded; readonly full source4 retained. Compiled approved policy fixtures are calibration-schema software tests, not genuine human gold/release/domain or performance acceptance. UI/regression/restoration/custody/closure checkpoint still independent.')
except Exception as failure:
    record.update(status='FAIL_HOLD_LATER_CLASSES_AND_F3',failure_type=type(failure).__name__,failure_message=str(failure))
    if current_run is not None and current_run.exists():
        directory=current_run/'failure-original-adb';directory.mkdir(exist_ok=False);captures={}
        for name in current_files:
            result=subprocess.run([str(ADB),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/'+name],capture_output=True,timeout=30)
            path=directory/name;path.write_bytes(result.stdout)
            info=dict(returncode=result.returncode,sha256=sha(path),bytes=len(result.stdout),scope='Failure-time bytes may be stale previous reports or cat errors; never accepted as current controls/results.')
            try:
                value=json.loads(result.stdout);info.update(valid_json=True,reported_status=value.get('status'))
            except (ValueError,UnicodeError):info['valid_json']=False
            captures[name]=info
        record['unaccepted_failure_captures']=captures
    raise
finally:
    record['finished_utc']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(record['status'],flush=True)
