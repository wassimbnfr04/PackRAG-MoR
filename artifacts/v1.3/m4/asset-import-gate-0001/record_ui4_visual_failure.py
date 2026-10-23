"""Keep real automated success separate from independently failed transition-time screenshots."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
execution=HERE/'device-local-asset-import-ui-0004-execution.json';value=read(execution)
assert value['status']=='PASS_F2_SYSTEM_PICKER_PHONE_CONTRACTS_VISUAL_REVIEW_PENDING_NOT_FULL_F2'
run=M4/'device-local-asset-import-ui-0004';device=read(run/'original-adb/m4-local-asset-import-ui.json')
assert device['status']=='PASS' and len(device['cases'])==8 and device['new_query_dispatch_observed'] is True
images={}
for name,digest in value['png_sha256'].items():
    path=run/'original-adb'/name;assert sha(path)==digest;images[name]=dict(sha256=digest,bytes=path.stat().st_size,review='FAIL: Android picker closing surface remains visible on the right and product text is cropped horizontally; not a settled readable full product viewport.')
target=HERE/'visual-inspection-ui0004.json';assert not target.exists()
note=('Actual UI0004 JUnit1/eight controls PASSED309.99s with original main/progress/two PNGs saved before switch, exact source4/owner50 unchanged, new query dispatch/new completion153tokens/cold init14913.25707ms/validated74°C[S1] answer. Actual requested recreation state STARTED and destruction/distinct instance/saved state/same ViewModel/picker foreground pass. Independent view_image inspection of both exact1080x2316 PNGs FAILS because snapshots catch Android picker exit surfaces/crop product text; automated PASS remains bounded and is not F2 visual acceptance. Preserve visual-inspection-ui0004.json FAIL and images unchanged. Next test-only stable-frame screenshot capture and short separate actual picker/progress/cancel/verified-template visual run; retain complete native/UI0004 only with exact selected-source and whole-product-APK proof, not relabeled new instrumentation. No source/APK change until current test is terminal/originals saved (now fulfilled). Full F2/adjacent guard repairs/matched final regressions/restoration/custody/closure still pending, F3/F4 held. Phone untouched window ended; keep PackRAG closed for background work, mobile data on, final packs owner supplied.')
record=dict(status='FAIL_VISUAL_ANDROID_PICKER_EXIT_TRANSITION_NOT_FULL_F2_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),execution_sha256=sha(execution),images=images,automated_scope='Actual eight controls/cold native PASS retained; two original screenshots fail independent visual acceptance.',note=note)
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as s:s.write('\n\n'+note+'\n')
print(record['status'])
