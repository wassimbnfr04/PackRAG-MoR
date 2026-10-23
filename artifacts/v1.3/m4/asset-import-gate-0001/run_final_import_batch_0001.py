"""Sequential final-build imports. Actual JUnit, deep validators and originals gate each step."""
import argparse, hashlib, json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
ADB=ROOT/'vendor/platform-tools/adb.exe'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);parser.add_argument('--prefix',required=True);args=parser.parse_args()
assert re.fullmatch(r'device-local-asset-final-import-[a-z0-9-]+',args.prefix)
build=M4/args.build;target=HERE/(args.prefix+'-execution.json');assert not target.exists() and build.parent==M4
assert read(HERE/(args.build+'-capture.json'))['variant']=='debug'
preparation=HERE/'final-import-regression-preparation-0002.json'
assert read(preparation)['status']=='PREPARED_FINAL_SOURCE_IMPORT_REGRESSIONS_NOT_EXECUTED_OR_ACCEPTED'
assert read(preparation)['final_build']==args.build
for name,info in read(preparation)['prepared_runners'].items():assert sha(HERE/name)==info['prepared_sha256']
assert read(HERE/'device-local-asset-adjacent-debug-0001-execution.json')['status']=='PASS_F2_FRESH_ADJACENT_BACKGROUND_VARIANT_NOT_FULL_F2'
for selection in ['management','query','sources','diagnostics','assets']:
    proof=read(HERE/('device-local-asset-adjacent-ui-0001-'+selection+'-execution.json'))
    assert proof['build']==args.build and proof['status']=='PASS_F2_FRESH_FOREGROUND_ADJACENT_CONTRACTS_VISUAL_REVIEW_PENDING_NOT_FULL_F2'
visual=read(HERE/'adjacent-ui-visual-review-0001.json')
assert visual['status']=='PASS_F2_ADJACENT_UI_VISIBLE_SCOPE_NOT_FULL_F2'
sources=read(build/'source-at-build-start.json')['files'];assert len(sources)==599
def unchanged():
    for name,value in sources.items():assert sha(ROOT/name)==value,name
unchanged()
plan=[
 ('faults','run_final_faults_installed_0001.py',3,28,['m4-local-asset-import-uri-faults.json','m4-local-asset-import-provider-cancel.json','m4-local-asset-import-path-recovery.json'],'PASS_F2_URI_PATH_CANCEL_28_CONTROLS_NOT_NATIVE_SYSTEM_PICKER_OR_FULL_F2'),
 ('walking','run_final_walking_installed_0001.py',1,7,['m4-local-asset-import-walking.json'],'PASS'),
 ('restart','run_final_restart_installed_0001.py',1,3,['m4-local-asset-import-process-death.json','m4-local-asset-import-process-death-progress.json'],'PASS_F2_ACTUAL_IMPORTING_SUBPROCESS_LOSS_AND_NATIVE_RECOVERY_NOT_ALL_SLOT_UI_OR_FULL_F2'),
 ('all-slots','run_final_all_slots_installed_0001.py',1,8,['m4-local-asset-import-all-slots.json','m4-local-asset-import-all-slots-progress.json'],'PASS_F2_ACTUAL_ALL_FOUR_FULL_SIZE_URI_IMPORT_AND_COLD_WARM_NATIVE_NOT_UI_OR_FULL_F2'),
 ('viewmodel','run_final_viewmodel_installed_0001.py',1,8,['m4-local-asset-import-viewmodel.json','m4-local-asset-import-viewmodel-progress.json'],'PASS_F2_BACKGROUND_PRODUCTION_VIEWMODEL_IMPORT_PRESERVATION_CANCEL_AND_NATIVE_NOT_PICKER_UI_OR_FULL_F2')]
record=dict(status='RUNNING_FINAL_SOURCE_IMPORTS_NOT_ACCEPTED',started_utc=datetime.now(timezone.utc).isoformat(),build=args.build,prefix=args.prefix,
 runner_sha256=sha(Path(__file__)),preparation_sha256=sha(preparation),commands=[],completed=[])
current_run=None;current_files=[]
def save():target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
def command(argv,label):
    print(args.prefix,label,'START',flush=True)
    with (HERE/(args.prefix+'-'+label+'.stdout.txt')).open('xb') as out,(HERE/(args.prefix+'-'+label+'.stderr.txt')).open('xb') as err:
        result=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=err)
    record['commands'].append(dict(argv=argv,returncode=result.returncode));save()
    assert result.returncode==0,'Hold later tests/F3; preserve failure-time bytes and repair'
    print(args.prefix,label,'PASS',flush=True)
try:
    source_proof=args.prefix+'-before-source.json'
    command([sys.executable,'-X','utf8',str(HERE/'prepare_full_sources.py'),'--build',args.build,'--output',source_proof,'--verify-only'],'before-source')
    command([sys.executable,'-X','utf8',str(HERE/'capture_known_guard.py'),'--output',args.prefix+'-before-known.json'],'before-known')
    for suffix,runner,methods,controls,files,status in plan:
        # A future user pause can be honored between tests without killing an active test.
        stop=HERE/(args.prefix+'-stop-after-current.request')
        if stop.exists():
            record.update(status='STOPPED_BETWEEN_TESTS_BY_EXPLICIT_REQUEST_NOT_ACCEPTED',next_selection=suffix);save();break
        unchanged();current_run=M4/(args.prefix+'-'+suffix);current_files=files
        record['active_selection']=suffix;save()
        argv=[sys.executable,'-X','utf8',str(HERE/runner),'--build',args.build,'--run',current_run.name]
        if suffix=='all-slots':argv+=['--source-preparation',source_proof]
        command(argv,suffix)
        execution=current_run/'execution.json' if suffix=='walking' else HERE/(current_run.name+'-execution.json')
        assert read(execution)['status']==status
        manifest=read(current_run/'instrumentation-manifest.json');assert manifest['status']=='PASS'
        assert manifest.get('transport')=='VERIFY_EXACT_INSTALLED_APKS_NO_REINSTALL'
        assert re.search(r'OK \('+str(methods)+r' tests?\)',(current_run/'instrumentation.txt').read_text())
        originals={}
        for name in files:
            path=current_run/'original-adb'/name;value=read(path);assert value['status']=='PASS'
            originals[name]=sha(path)
        unchanged();record['completed'].append(dict(selection=suffix,methods=methods,controls=controls,run=current_run.name,
            execution_sha256=sha(execution),manifest_sha256=sha(current_run/'instrumentation-manifest.json'),original_sha256=originals));save()
        print('ACCEPTED_FINAL_IMPORT_ORIGINALS',suffix,methods,controls,flush=True)
    else:
        command([sys.executable,'-X','utf8',str(HERE/'prepare_full_sources.py'),'--build',args.build,'--output',args.prefix+'-after-source.json','--verify-only'],'after-source')
        command([sys.executable,'-X','utf8',str(HERE/'capture_known_guard.py'),'--output',args.prefix+'-after-known.json'],'after-known')
        unchanged();record.update(status='PASS_FINAL_SOURCE_IMPORT_7_METHODS_54_CONTROLS_NOT_FULL_F2',
            scope='Fresh final599 inputs, actual7 methods/54 controls; deep semantic validators retained, originals saved before next step; real pinned LFM walking/restart/allslot/ViewModel paths. Installed APK identities checked without reinstall, owner50/source4 unchanged. Historical results/runners unchanged. Watchdogs are functional safety bounds, not performance acceptance. Whole F2 policy/restoration/custody/cleanup/closure/checkpoint independent.')
except Exception as failure:
    record.update(status='FAIL_HOLD_LATER_IMPORTS_AND_F3',failure_type=type(failure).__name__,failure_message=str(failure))
    if current_run is not None and current_run.exists():
        directory=current_run/'parent-failure-original-adb';directory.mkdir(exist_ok=False);captures={}
        for name in current_files:
            out=subprocess.run([str(ADB),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/'+name],capture_output=True,timeout=30)
            path=directory/name;path.write_bytes(out.stdout)
            info=dict(returncode=out.returncode,sha256=sha(path),bytes=len(out.stdout),scope='Unaccepted failure-time bytes; may be stale earlier results or cat errors. Not new PASS.')
            try:info.update(valid_json=True,reported_status=json.loads(out.stdout).get('status'))
            except (ValueError,UnicodeError):info['valid_json']=False
            captures[name]=info
        record['unaccepted_failure_captures']=captures
    raise
finally:record['finished_utc']=datetime.now(timezone.utc).isoformat();save()
print(record['status'],flush=True)
