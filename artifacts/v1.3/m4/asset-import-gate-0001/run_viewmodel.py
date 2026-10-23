"""Frozen physical background ViewModel/native gate; no Activity or foreground window."""
import argparse,hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);parser.add_argument('--run',required=True);args=parser.parse_args()
build=M4/args.build;run=M4/args.run;target=HERE/(args.run+'-execution.json');assert build.parent==M4 and run.parent==M4 and not run.exists() and not target.exists()
assert read(HERE/'all-slots-complete-0001.json')['status']=='PASS_F2_ALL_SLOT_API_NATIVE_ITERATION_NOT_FULL_F2'
host=read(HERE/(args.build+'-capture.json'));assert host['status']=='PASS_F2_API_ITERATION_HOST_APK_CONTRACTS_NOT_DEVICE_OR_F2_ACCEPTANCE' and host['variant']=='debug'
sources=read(build/'source-at-build-start.json')['files']
for name,value in sources.items():assert sha(ROOT/name)==value,name
files=['m4-local-asset-import-viewmodel.json','m4-local-asset-import-viewmodel-progress.json']
commands=[
    [sys.executable,'-X','utf8',str(HERE/'prepare_full_sources.py'),'--build',args.build,'--output',args.run+'-before-source.json','--verify-only'],
    [sys.executable,'-X','utf8','-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(build),'--run',str(run),'--class-name','org.packrag.product.LocalAssetImportViewModelDeviceTest','--result-file',files[0],'--timeout','2400','--variant','debug'],
    [sys.executable,'-X','utf8','-m','scripts.v13_collect_phone_results','--run',str(run),'--files',','.join(files)],
    [sys.executable,'-X','utf8',str(HERE/'prepare_full_sources.py'),'--build',args.build,'--output',args.run+'-after-source.json','--verify-only'],
    [sys.executable,'-X','utf8',str(HERE/'capture_known_guard.py'),'--output',args.run+'-after-known-guard.json']]
record=dict(status='RUNNING',started_utc=datetime.now(timezone.utc).isoformat(),runner_sha256=sha(Path(__file__)),build=args.build,run=args.run,commands=[])
try:
    for i,command in enumerate(commands):
        print(args.run,'stage',i,'START',flush=True)
        with (HERE/(args.run+f'-stage-{i}.stdout.txt')).open('xb') as out,(HERE/(args.run+f'-stage-{i}.stderr.txt')).open('xb') as err:r=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
        record['commands'].append(dict(argv=command,returncode=r.returncode));target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');assert r.returncode==0,'Hold UI/F3; preserve failure and repair'
        print(args.run,'stage',i,'PASS',flush=True)
    collection=read(run/'collected-results.json');assert set(collection['saved_sha256'])==set(files)
    device=read(run/'original-adb'/files[0]);assert device['status']=='PASS' and device['variant']=='debug'
    for name in files:
        p=run/'original-adb'/name;assert sha(p)==collection['saved_sha256'][name];value=read(p);assert value['status']=='PASS' and value['cases']==device['cases']
    expected_cases=['actual-native-completed-answer-and-owned-result-context','wrong-hash-rejection-preserves-file-answer-trace-submission-and-result-id',
        'generic-source-rejection-recovery-preserves-owned-completion','actual-observed-partial-byte-progress-and-cooperative-read-cancel-preserve-completion',
        'actual-transported-open-cancel-awaits-cleanup-and-preserves-completion','successful-verified-import-preserves-completion-and-invalidates-other-cached-asset-checks',
        'independent-four-pin-recheck-preserves-completed-result','actual-post-import-cold-native-answer-uses-new-owned-result-id']
    assert [case['id'] for case in device['cases']]==expected_cases and all(case['passed'] is True for case in device['cases'])
    assert device['owner_registry_and_model_sha256']==read(HERE/'before.json')['owner_public_file_sha256'] and device['guards_unchanged'] is True
    assert device['observed_partial_copy_bytes']==128
    for label in ['reading_cancel_dispatch_ms','opening_cancel_dispatch_ms']:assert 0<device[label]<1000
    for label in ['before','after']:assert '74 °C' in device['answer_'+label] and '[S1]' in device['answer_'+label] and 1<=device['emitted_tokens_'+label]<=512
    assert device['completed_result_id_before']!=device['completed_result_id_after'] and device['initialization_ms_after']>0
    assert device['actual_weight_inference'] is True and device['raw_reasoning_persisted'] is False
    for when in ['before','after']:assert read(HERE/(args.run+'-'+when+'-source.json'))['source_sha256']==read(HERE/'full-source-preparation-0001.json')['source_sha256']
    for name,value in sources.items():assert sha(ROOT/name)==value,name
    record.update(status='PASS_F2_BACKGROUND_PRODUCTION_VIEWMODEL_IMPORT_PRESERVATION_CANCEL_AND_NATIVE_NOT_PICKER_UI_OR_FULL_F2',finished_utc=datetime.now(timezone.utc).isoformat(),original_sha256=collection['saved_sha256'],cases=expected_cases,
        scope='Actual production ViewModel and real JNI answers before/after imports, strict identical completed answer/trace/submission/id preservation on typed/generic failure, cooperative cancellation and success; actual128-byte progress and main cancel dispatch observations. Cancellation waits for real cleanup/commit rather than pretending immediate rollback. Test-only Application filesDir isolation, no owner default asset writes. Source4/owner50 hashes unchanged. No Activity/system picker/foreground UI/full F2/M4/product/performance or arbitrary IPC bound acceptance.')
except Exception as e:
    record.update(status='FAIL',finished_utc=datetime.now(timezone.utc).isoformat(),failure_type=type(e).__name__,failure_message=str(e))
    if run.exists():
        directory=run/'failure-original-adb';directory.mkdir(exist_ok=False)
        r=subprocess.run([str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell','run-as','org.packrag.product','cat','files/'+files[1]],capture_output=True,timeout=30)
        record['failure_progress_returncode']=r.returncode
        if r.returncode==0:
            p=directory/files[1];p.write_bytes(r.stdout);record['failure_progress_sha256']=sha(p)
    raise
finally:target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(record['status'],flush=True)
