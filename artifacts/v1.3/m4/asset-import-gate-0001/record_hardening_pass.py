"""Record actual28 controls without promoting the pending native/full-F2 gate."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'hardening-pass-0001.json';assert not target.exists()
result=read(HERE/'device-local-asset-import-faults-0002-execution.json')
assert result['status']=='PASS_F2_URI_PATH_CANCEL_28_CONTROLS_NOT_NATIVE_SYSTEM_PICKER_OR_FULL_F2' and result['case_count']==28
run=M4/'device-local-asset-import-faults-0002';cancellation=read(run/'original-adb/m4-local-asset-import-provider-cancel.json')
assert cancellation['actual_typed_cancellable_provider_dispatch'] is True
time=datetime.now(timezone.utc).isoformat()
note=f'Current M4F2 at {time}: corrected0063 actual fault suite0002 PASS three methods/28 controls49.491 whole-instrumentation seconds. Actual grants/revocation/rejected sizes/hash/wrong slot/error/metadata lies, controlled short pipe, precommit and late-commit cancellation, Android leaf/parent/root/marker/stage/namespace symlinks, validated same-process startup reconciliation/legacy preservation and explicit controlled sync fault all pass. Actual typed-cancellable branch/pipe counters are asserted; blocked-pipe copy observes{cancellation["timings"]["actual_copied_bytes_before_pipe_cancel"]}bytes before cancel. Main cancellation dispatch observations are{cancellation["timings"]["pipe_main_cancel_dispatch_ms"]}ms read/{cancellation["timings"]["opening_main_cancel_dispatch_ms"]}ms opening, with15s completion watchdog; these are specific cooperative-provider functional bounds, not M8 speed or arbitrary-provider IPC guarantees. All three original JSON files are saved/hash bound and known50 public owner-file hashes match. First0001 FAIL and its two partial originals/25 assertions remain unchanged; its old short-pipe label is not accepted as physical pipe evidence. Real native walking0003 on identical0063 is now RUNNING in the serial gate; do not progress restart/all-slot/UI until it passes. Still not complete F2: actual process-death, all4 artifact imports, ViewModel/system-picker/progress/cancel UI, approved-policy/adjacent/F1 regressions, restoration/custody/closure/exact checkpoint remain before F3; F3/F4/later software/release/delivery remain. Owner final packs excluded; mobile data stays on, PackRAG stays closed for background tests.'
record=dict(status='PASS28_ACTUAL_F2_FAULT_CONTROLS_NATIVE_REGRESSION_PENDING_NOT_FULL_F2',recorded_utc=time,
    fault_execution_sha256=sha(HERE/'device-local-asset-import-faults-0002-execution.json'),original_sha256=result['original_sha256'],
    cancellation_observations=cancellation['timings'],scope='Includes explicitly labelled byte count in the observation dictionary; only *_ms fields are timings. No actual process death, all-slot/full native or system picker acceptance in the fault suite.',note=note)
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(record['status'],flush=True)
