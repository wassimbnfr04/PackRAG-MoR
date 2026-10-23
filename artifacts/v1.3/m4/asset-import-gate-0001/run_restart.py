"""Actual owned importing subprocess death and native recovery; original before switch."""
import argparse,hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);parser.add_argument('--run',required=True);args=parser.parse_args()
build=M4/args.build;run=M4/args.run;assert build.parent==M4 and run.parent==M4 and not run.exists()
target=HERE/(args.run+'-execution.json');assert not target.exists()
assert read(HERE/'hardening-native-complete-0001.json')['status']=='PASS_INTEGRATED_F2_HARDENING_ITERATION_NOT_FULL_F2'
host=read(HERE/(args.build+'-capture.json'));assert host['status']=='PASS_F2_API_ITERATION_HOST_APK_CONTRACTS_NOT_DEVICE_OR_F2_ACCEPTANCE'
assert host['variant']=='debug' and host['host_xml_totals']==dict(tests=73,failures=0,errors=0,skipped=0)
sources=read(build/'source-at-build-start.json')['files']
for name,value in sources.items():assert sha(ROOT/name)==value,name
files=['m4-local-asset-import-process-death.json','m4-local-asset-import-process-death-progress.json']
commands=[
    [sys.executable,'-X','utf8','-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(build),'--run',str(run),
     '--class-name','org.packrag.product.LocalAssetImportProcessDeathDeviceTest','--result-file',files[0],'--timeout','2400','--variant','debug'],
    [sys.executable,'-X','utf8','-m','scripts.v13_collect_phone_results','--run',str(run),'--files',','.join(files)],
    [sys.executable,'-X','utf8',str(HERE/'capture_known_guard.py'),'--output',args.run+'-after-known-guard.json']]
record=dict(status='RUNNING',started_utc=datetime.now(timezone.utc).isoformat(),build=args.build,run=args.run,variant='debug',runner_sha256=sha(Path(__file__)),commands=[])
try:
    for i,command in enumerate(commands):
        print(args.run,'stage',i,'START',flush=True);start=datetime.now(timezone.utc).isoformat()
        with (HERE/(args.run+f'-stage-{i}.stdout.txt')).open('xb') as out,(HERE/(args.run+f'-stage-{i}.stderr.txt')).open('xb') as err:
            result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
        record['commands'].append(dict(argv=command,started_utc=start,finished_utc=datetime.now(timezone.utc).isoformat(),returncode=result.returncode))
        target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');assert result.returncode==0,'Hold later F2/all-slot/UI; preserve failure/progress originals and repair'
        print(args.run,'stage',i,'PASS',flush=True)
    expected=read(HERE/'before.json')['owner_public_file_sha256'];collection=read(run/'collected-results.json')
    assert set(collection['saved_sha256'])==set(files)
    for name in files:
        raw=run/'original-adb'/name;assert sha(raw)==collection['saved_sha256'][name]
        device=read(raw);assert device['status']=='PASS' and device['variant']=='debug' and device['cases']==read(run/files[0])['cases']
        assert device['owner_registry_and_model_sha256']==expected and device['guards_unchanged'] is True
        assert device['actual_weight_inference'] is True and device['raw_reasoning_persisted'] is False
    device=read(run/files[0]);assert re.fullmatch('[0-9a-f-]{36}',device['test_id'])
    assert [case['id'] for case in device['cases']]==['actual-importing-process-death-'+point for point in ['COPYING','COMMITTING','COMMITTED']]
    pids=set()
    for case,point in zip(device['cases'],['COPYING','COMMITTING','COMMITTED'],strict=True):
        assert case['passed'] is True and case['probe']['state']=='KILLING' and case['probe']['point']==point and case['probe']['test_id']==device['test_id']
        assert case['probe']['copied_bytes']==5443 and case['probe']['expected_bytes']==5443
        assert case['probe']['pid'] not in pids;pids.add(case['probe']['pid'])
        committed=point=='COMMITTED';assert case['commit_survived'] is committed and case['repair_import_required'] is (not committed)
        assert case['namespace_existed_before_reopen'] is True and case['stage_count_before_reopen']==(0 if committed else 1)
        if committed:
            assert case['stage_sha256_before_reopen'] is None and case['fully_pinned_abandoned_stage_never_promoted'] is None
            assert case['final_sha256_before_reopen']=='ea663864491de7ade391839479860ca95541f892f72665c73251fbd4643b1bef'
        else:
            assert case['stage_sha256_before_reopen']=='ea663864491de7ade391839479860ca95541f892f72665c73251fbd4643b1bef'
            assert case['fully_pinned_abandoned_stage_never_promoted'] is True
            assert case['final_sha256_before_reopen']==hashlib.sha256(b'older').hexdigest()
        assert '74 °C' in case['answer'] and '[S1]' in case['answer'] and 1<=case['emitted_tokens']<=512 and case['initialization_ms']>0
    for name,value in sources.items():assert sha(ROOT/name)==value,name
    record.update(status='PASS_F2_ACTUAL_IMPORTING_SUBPROCESS_LOSS_AND_NATIVE_RECOVERY_NOT_ALL_SLOT_UI_OR_FULL_F2',finished_utc=datetime.now(timezone.utc).isoformat(),
        original_sha256=collection['saved_sha256'],probe_pids=sorted(pids),checkpoint_ids=[case['id'] for case in device['cases']],
        scope='Actual debug unexported importing subprocess dies at3 checkpoints; fresh main ProductSession cleanup/native cold answers. Whole phone/main instrumentation stay alive. Child PID/distinctness recorded; main/probe PID inequality is asserted by frozen device source, main PID is not a persisted result field. Precommit fully valid stage is deleted, never promoted; postcommit no stage makes that field null/not applicable. No physical power-loss/cache-failure/cross-process warm-model lease, system picker, all-slot or full F2/M4/product/performance acceptance.')
except Exception as failure:
    record.update(status='FAIL',finished_utc=datetime.now(timezone.utc).isoformat(),failure_type=type(failure).__name__,failure_message=str(failure));raise
finally:target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(record['status'],flush=True)
