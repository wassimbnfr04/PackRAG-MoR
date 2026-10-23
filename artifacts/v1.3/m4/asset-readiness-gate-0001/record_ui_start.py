"""Record actual verified background retry and announced foreground start only."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'foreground-start-0001.json';assert not target.exists()
adjacent=read(HERE/'device-local-assets-adjacent-0002-verified.json')
assert adjacent['status']=='PASS_F1_ADJACENT_INDEPENDENT_ORIGINAL_CONTRACT_CHECK_NOT_CLOSURE' and adjacent['methods']==5
assert adjacent['owner_public_file_sha256']==read(HERE/'guarded-retry-preparation.json')['owner_public_file_sha256']
execution=read(HERE/'ui-execution-0001.json');assert execution['status']=='RUNNING' and execution['owner_quote']=='Yes, announce when it starts'
inputs=read(M4/'build-0056/source-at-build-start.json')['files'];assert len(inputs)==579
for name,value in inputs.items():assert sha(ROOT/name)==value,name
record=dict(status='RUNNING_ACTUAL_F1_FOREGROUND_AFTER_BACKGROUND_RETRY_VERIFICATION_NOT_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    adjacent_methods=5,adjacent_whole_instrumentation_seconds=adjacent['whole_instrumentation_seconds'],
    adjacent_verified_sha256=sha(HERE/'device-local-assets-adjacent-0002-verified.json'),
    owner_quote=execution['owner_quote'],readiness=execution['readiness'],
    announcement='The screen test starts now. Please leave the phone unlocked and untouched for about five minutes. Mobile data stays on.',
    scope='The unchanged adjacent retry passed and all five originals were independently collected/checked before UI installation. Its50 public guards preserve the explicit post-launch cf140 baseline. Earlier failed adjacent0001 and its whole-session registry exception remain unchanged. UI automated/original PNG/manual visual, both compiled-policy phases, restored development consent, final owner/source checks and closure/checkpoint remain required. F2 implementation not started.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
note=f'Current M4F1 at {record["recorded_utc"]}: unchanged development adjacent retry0002 passes all five methods in {record["adjacent_whole_instrumentation_seconds"]} whole-instrumentation seconds. All five original reports are saved and independently source/APK/hash/contract checked; all50 public owner-file guards match the explicit post-launch baseline. Development core0002 remains accepted within its earlier pre-launch baseline. The failed adjacent0001 is retained and whole-session default-registry byte preservation remains false. Awake/unlocked observations pass, and the owner-authorized roughly five-minute untouched window is announced. Actual local-assets UI0001 is running on0056; no UI or F1 acceptance yet. Next: original UI report/two PNGs and actual visual inspection, policy0057 core/adjacent, restored0056 consent, final source/known-owner-file checks, closure and exact checkpoint. F2/F3/F4 and later software/release/delivery remain. Final knowledge content is owner supplied; mobile data stays on; functional times are not performance benchmarks.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;head,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(head+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(record['status'])
