"""Await actual state-changing UI dispatch, then completion; expectations stay fixed."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
target=HERE/'ui-action-dispatch-repair.json';assert not target.exists()
old=read(M4/'build-0050/source-at-build-start.json')['files']
for n,v in old.items():assert sha(ROOT/n)==v,n
assert read(M4/'device-ui-diagnostics-retained-0003/partial-collected-results.json')['method_status_codes']['capturedControlsSurviveRealGenerationEditsRecreationAndSourceNavigation']==0
folder=HERE/'ui-action-dispatch-before';folder.mkdir(exist_ok=False);deltas={}
for stem in ['SourceDetailsUiTest','QueryControlsUiTest']:
    n=f'product/android/app/src/androidTest/java/org/packrag/product/{stem}.kt';p=ROOT/n;before_bytes=p.read_bytes();(folder/(stem+'.kt')).write_bytes(before_bytes)
    source=p.read_text(encoding='utf-8')
    before='fun settle() { compose.waitUntil(600_000)';after='fun settle() { compose.waitForIdle();compose.waitUntil(600_000)'
    assert source.count(before)==1;source=source.replace(before,after)
    before='fun click(tag:String) { compose.onNodeWithTag(tag).performScrollTo().performClick() }'
    if stem=='SourceDetailsUiTest':
        after='''fun click(tag:String) {
            val previous=model.state.value
            compose.onNodeWithTag(tag).performScrollTo().performClick()
            // All tagged clicks in this method invoke a ViewModel action.
            // Observe the action's state transition before testing its completion.
            compose.waitUntil(30_000) { model.state.value !== previous }
        }'''
    else:
        after='''fun click(tag:String) {
            val previous=model.state.value
            compose.onNodeWithTag(tag).performScrollTo().performClick()
            // Checkbox changes only local form state; submit changes ViewModel state synchronously when dispatched.
            if(tag=="query-submit") compose.waitUntil(30_000) { model.state.value !== previous }
        }'''
    assert source.count(before)==1;source=source.replace(before,after);p.write_text(source,encoding='utf-8');deltas[n]=dict(before=hashlib.sha256(before_bytes).hexdigest(),after=sha(p))
for n,v in old.items():
    if n not in deltas:assert sha(ROOT/n)==v,n
record=dict(status='TWO_UI_ACTION_DISPATCH_WAITS_STRENGTHENED_NEW_VALIDATION_REQUIRED',recorded_utc=datetime.now(timezone.utc).isoformat(),exact_test_deltas=deltas,unchanged_android_inputs=572,
    actual_new_query_observation=read(M4/'device-ui-diagnostics-retained-0003/m4-ui-query-resubmission-observation.json'),
    diagnosis='0003 source method fails at first accepted-answer assertion with null after old settle before actual action completion. Source/Query old helpers omit waitForIdle unlike passing PackManagement. Await actual state object replacement for state-changing tags, then idle/not-busy; keep all answer, active-state, context, source and owner assertions. No direct model calls or product edits. Original0002 timing cause is not retrospectively proved: new0003 immediate observation was already busy.',
    validation='Fresh0052/0053 matched builds, all four UI methods/visual/full37/full30/restoration/parity/closure required; previous failures remain unchanged.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
message='E3 current10 October20:16 UTC: UI0003 finished four methods/one failure124.251s. Corrected query-controls PASSES actual generated answer/recreation/source/final edited-context distinct completion with NO_RELEVANT_EVIDENCE; immediate observation already busy, so prior0002 race is not retroactively proved. SourceDetails first query fails ANSWER_ACCEPTED versus null before completion; three completed passing originals/PNGs/ownership observation saved, overall FAIL retained. Exact SourceDetails/Query helper repair now waits actual ViewModel state replacement after action click and then idle/completion; all expectations unchanged,572 other Android inputs unchanged. Fresh0052/53 and UI0004/full gates required. No phone test running; F/later held; mobile data unchanged.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;text=p.read_text(encoding='utf-8-sig');first,rest=text.split('\n',1);p.write_text(first+'\n\n'+message+'\n'+rest,encoding='utf-8')
for name in ['docs/v1.3/M4E3_METHODS.md','docs/v1.3/M4E3_EVIDENCE_INDEX.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','DECISIONS.md']:
    with (ROOT/name).open('a',encoding='utf-8') as f:f.write('\n\n'+message+'\n\nui-action-dispatch-repair.json binds exact two pre/post test bytes. No production callback/output or expected answer is changed. Await-state reference means an actual submitted action must be observed, including fast no-generation outcomes that need not expose a busy interval; ignored actions fail30s rather than consume stale prior state.\n')
print('Two test-only action dispatch waits repaired, all expected outcomes unchanged')
