"""Preserve two actually successful method originals from an overall failed F2 suite."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4';RUN=M4/'device-local-asset-import-faults-0001'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'fault-partial-0001.json';assert not target.exists()
manifest=read(RUN/'instrumentation-manifest.json');assert manifest['status']=='FAIL'
raw=(RUN/'instrumentation.txt').read_text(encoding='utf-8');assert 'Tests run: 3,  Failures: 1' in raw and 'Time: 40,364' in raw
names={'m4-local-asset-import-uri-faults.json':('actualUriRejectionsMetadataShortStreamsAndCommitCancellationPreservePinnedFinal',15),
       'm4-local-asset-import-path-recovery.json':('actualAndroidSymlinksOwnedStartupRecoveryAndSyncFaultNeverPromoteUnsafeStages',10)}
destination=RUN/'partial-collected-results';assert not destination.exists();destination.mkdir();saved={};commands=[]
expected=read(HERE/'before.json')['owner_public_file_sha256']
for name,(method,count) in names.items():
    assert re.search('INSTRUMENTATION_STATUS: test='+re.escape(method)+r'\s+INSTRUMENTATION_STATUS_CODE: 0',raw)
    argv=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell','run-as','org.packrag.product','cat','files/'+name]
    out=subprocess.run(argv,capture_output=True,check=True,timeout=30);(destination/name).write_bytes(out.stdout)
    device=json.loads(out.stdout);assert device['status']=='PASS' and len(device['cases'])==count and all(case['passed'] is True for case in device['cases'])
    assert device['owner_registry_and_model_sha256']==expected and device['guards_unchanged'] is True
    saved[name]=sha(destination/name);commands.append(dict(argv=argv,returncode=out.returncode,stderr=out.stderr.decode('utf-8',errors='replace')))
guard=subprocess.run([str(ROOT/'.venv-pack/Scripts/python.exe'),'-X','utf8',str(HERE/'capture_known_guard.py'),'--output','failed-faults-0001-after-guard.json'],cwd=ROOT,capture_output=True,check=True)
record=dict(status='OVERALL_FAIL_TWO_COMPLETED_METHOD_ORIGINALS_PRESERVED_NOT_F2_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    original_failure_sha256={name:sha(RUN/name) for name in ['instrumentation.txt','instrumentation-manifest.json']},
    saved_partial_original_sha256=saved,completed_control_count=25,commands=commands,
    post_suite_known50_guard_sha256=sha(HERE/'failed-faults-0001-after-guard.json'),
    observed_failure='Cancellable method line133 asserts blocked future is unfinished after first progress and200ms; actual future already done. No per-chunk byte/result trace exists for that failed method; do not infer the future returned a success instead of an exception.',
    code_review_hypothesis='Only cancellable openAssetFile override creates the controlled pipe; openFile fallback serves a regular full template. ContentResolver read-mode may route through typed-asset defaults. Explicit typed override/dispatch counters and a cooperative pipe are required; actual corrected run must establish the branch.',
    scope='Failed suite40.364s/three methods/one failure remains immutable. Passing two method originals prove25 controls only. Failed method has no accepted original; native walking0003 was not dispatched because serial sequence stopped. No new native, UI, process-death/all-slot or complete F2 acceptance.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
note=f'F2 fault suite0001 on0062 at {record["recorded_utc"]} terminalFAIL three methods/one failure40.364s. Actual URI rejections15 and Android path/recovery10 controls PASS; both exact originals saved as explicitly partial, overall suite unchangedFAIL. All known50 owner-file hashes match afterward. '+record['observed_failure']+' '+record['code_review_hypothesis']+' Native walking0003 is not executed; stop further hardening/UI progression until this harness failure is diagnosed/repaired/rerun. No app/native failure is attributed from this assertion alone.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(record['status'],flush=True)
