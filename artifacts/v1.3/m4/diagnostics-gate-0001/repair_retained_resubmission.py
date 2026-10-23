"""Strengthen final query UI ownership synchronization; preserve failed source/run."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
target=HERE/'retained-resubmission-repair.json';assert not target.exists()
old=read(M4/'build-0048/source-at-build-start.json')['files']
for n,v in old.items():assert sha(ROOT/n)==v,n
assert read(M4/'device-ui-diagnostics-retained-0002/partial-collected-results.json')['status']=='SAVED_THREE_COMPLETED_METHODS_OVERALL_SUITE_FAIL'
name='product/android/app/src/androidTest/java/org/packrag/product/QueryControlsUiTest.kt';p=ROOT/name
saved=HERE/'retained-resubmission-before/QueryControlsUiTest.kt';saved.parent.mkdir(exist_ok=False);saved.write_bytes(p.read_bytes())
source=p.read_text(encoding='utf-8')
before='            replace("query-question",question);click("query-submit");settle()'
after='''            replace("query-question",question)
            compose.onNodeWithTag("query-date").performScrollTo().assertTextContains("2028-02-29")
            compose.onNodeWithTag("query-jurisdiction").performScrollTo().assertTextContains("MA-01")
            val previousCompletion=requireNotNull(model.state.value.completedResultId)
            click("query-submit")
            val immediate=model.state.value
            val resubmission=JSONObject().put("previous_completion_id",previousCompletion)
                .put("immediate_busy",immediate.busy).put("immediate_completion_id",immediate.completedResultId ?: JSONObject.NULL)
                .put("immediate_answer_state",immediate.answer?.state ?: JSONObject.NULL)
                .put("immediate_submitted_date",immediate.submission?.query?.asOf ?: JSONObject.NULL)
                .put("immediate_submitted_jurisdiction",immediate.submission?.query?.jurisdiction ?: JSONObject.NULL)
            val observation=File(context.filesDir,"m4-ui-query-resubmission-observation.json")
            observation.writeText(resubmission.put("status","OBSERVED_BEFORE_COMPLETION_WAIT_NOT_PASS").toString(2),Charsets.UTF_8)
            // A posted UI tap can leave the prior non-busy result visible briefly.
            // Wait for this submitted context AND a distinct completed result; a fast abstention need not expose busy.
            compose.waitUntil(600_000) {
                val value=model.state.value
                !value.busy && value.completedResultId!=null && value.completedResultId!=previousCompletion &&
                    value.submission?.query?.raw==question && value.submission?.query?.asOf=="2028-02-29" &&
                    value.submission?.query?.jurisdiction=="MA-01"
            }
            settle()
            assertNotEquals(previousCompletion,model.state.value.completedResultId)
            resubmission.put("status","NEW_COMPLETION_OBSERVED_ASSERTIONS_PENDING")
                .put("new_completion_id",model.state.value.completedResultId)
                .put("new_answer_state",model.state.value.answer?.state)
            observation.writeText(resubmission.toString(2),Charsets.UTF_8)'''
assert source.count(before)==1;source=source.replace(before,after)
before='            passed("later-submit-uses-edited-controls-and-replaces-old-answer")'
after=before+'\n            observation.writeText(resubmission.put("status","PASS_NEW_COMPLETION_EDITED_CONTEXT_ABSTENTION").toString(2),Charsets.UTF_8)'
assert source.count(before)==1;source=source.replace(before,after)
p.write_text(source,encoding='utf-8')
for n,v in old.items():
    if n!=name:assert sha(ROOT/n)==v,n
target.write_text(json.dumps(dict(status='TEST_OWNERSHIP_WAIT_REPAIRED_REVALIDATION_REQUIRED',recorded_utc=datetime.now(timezone.utc).isoformat(),
    changed_source=name,before_sha256=sha(saved),after_sha256=sha(p),unchanged_android_inputs=573,
    unchanged_expected_answer='NO_RELEVANT_EVIDENCE',failure_run='device-ui-diagnostics-retained-0002',
    scope='Busy false alone can observe previous completion; diagnosis is a source-supported hypothesis pending actual immediate/new ownership observations. No product/runtime/test expectation changes; fresh matched builds and all four UI methods required. Earlier suite remains FAIL.'),indent=2)+'\n',encoding='utf-8')
message='E3 current10 October20:09 UTC: retained UI0002 FINISHED four methods/one failure/200.195s. Three passing originals/two PNGs saved separately; overall FAIL unchanged. Final query assertion observes ANSWER_ACCEPTED instead of NO_RELEVANT_EVIDENCE. Old test busy-false wait can observe old completion after a posted tap; test-only strengthening now requires distinct completedResultId AND exact edited question/date/jurisdiction, keeps all answer assertions and adds immediate/new state observations. Hypothesis pending actual evidence, not declared app fix. Exact one test source changed/573 other Android inputs unchanged. Fresh debug0050/demo0051, actual four-method UI/visual and full37/30/restoration/parity/closure required before F. No phone test running; no radio/owner-file changes.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;text=p.read_text(encoding='utf-8-sig');first,rest=text.split('\n',1);p.write_text(first+'\n\n'+message+'\n'+rest,encoding='utf-8')
for name in ['docs/v1.3/M4E3_METHODS.md','docs/v1.3/M4E3_EVIDENCE_INDEX.md','FULL_DOCUMENTATION_WORKING.md','DECISIONS.md']:
    with (ROOT/name).open('a',encoding='utf-8') as f:f.write('\n\n'+message+'\n\nDetailed exact source repair and pre-repair bytes: diagnostics-gate-0001/retained-resubmission-repair.json and retained-resubmission-before/QueryControlsUiTest.kt. The three partial originals are solely completed-method evidence; failed query JSON is not promoted. No full-background driver started.\n')
print('Exact one test synchronization repair; fresh validation required')
