"""Record only completed physical process-recovery evidence; not full F2 acceptance."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'restart-complete-0001.json';assert not target.exists()
run='device-local-asset-import-process-death-0001';execution=HERE/(run+'-execution.json')
record=read(execution)
assert record['status']=='PASS_F2_ACTUAL_IMPORTING_SUBPROCESS_LOSS_AND_NATIVE_RECOVERY_NOT_ALL_SLOT_UI_OR_FULL_F2'
raw=M4/run/'original-adb/m4-local-asset-import-process-death.json';device=read(raw)
assert device['status']=='PASS' and len(device['cases'])==3
assert sha(raw)==record['original_sha256'][raw.name]
time=datetime.now(timezone.utc).isoformat()
note=f'Current M4F2 actual importing-process recovery iteration PASSED at {time}: build0065/frozen591 Android inputs/73 host contracts and device-process-death0001 passed all3 actual importing subprocess SIGKILL checkpoints COPYING, COMMITTING and COMMITTED. Original main/progress JSON saved before any APK/source switch; driver validates their hashes, source identities and known50 owner-file hashes against the explicit post-F1 baseline. Two precommit cases preserved deliberately different old5byte final, independently observed fully correct5443byte abandoned stage, removed that stage on fresh ProductSession startup without promoting it, rejected generation on bad final, then repaired through the real granted URI. Postcommit exact final survived and required no repair; abandoned-stage-promotion field is null/not applicable there. Each recovery produced a real cold accepted synthetic74°C[S1] answer through retrieval/admission/selection/LFM2.5/reasoning removal/citation validation. Child PIDs and checkpoints are persisted; actual binder disconnect and main/child PID inequality asserted in frozen source (main PID not persisted). Phone/main instrumentation remain alive; this is not physical power loss, whole-phone/main restart or cross-process warm-reader lease proof. F2 actual four full-size URI imports, ViewModel/system picker UI, approved-policy/retained regressions/restoration/custody/closure/exact checkpoint still remain; full M4/product/release not accepted. Next: actual full-size four-slot URI transport/native iteration, isolated destinations and read-only known-owner source copies into newly owned test UID storage. Final knowledge packs remain owner supplied, mobile data stays on, PackRAG stays closed until a separately announced UI window.'
result=dict(status='PASS_F2_PROCESS_RECOVERY_ITERATION_NOT_FULL_F2',recorded_utc=time,execution_sha256=sha(execution),
    original_sha256=record['original_sha256'],cases=device['cases'],note=note)
target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(result['status'])
