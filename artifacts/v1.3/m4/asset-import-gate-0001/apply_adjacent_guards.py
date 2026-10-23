"""Apply previously validated guard-only proposals only after physical visual acceptance."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
target=HERE/'adjacent-guard-applied-0001.json';assert not target.exists()
review=HERE/'visual-inspection-visual0003.json'
assert json.loads(review.read_text())['status']=='PASS_VISUAL_SEPARATE_PICKER_TEMPLATE_SCOPE_NOT_FULL_F2'
preparation=HERE/'adjacent-guard-preparation-0001.json';proposal=json.loads(preparation.read_text())
assert proposal['status']=='PREPARED_VALIDATED_NOT_APPLIED_OR_ACCEPTED' and len(proposal['files'])==11
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
pending=[]
for name,value in proposal['files'].items():
    path=ROOT/name;source=HERE/'adjacent-guard-proposals-0001'/(path.name+'.proposed')
    assert sha(path)==value['original_sha256'] and sha(source)==value['proposed_sha256']
    pending.append((path,source.read_bytes(),value['proposed_sha256']))
# All closed source paths and proposal hashes validate before any source mutation.
for path,payload,expected in pending:path.write_bytes(payload);assert sha(path)==expected
note=('F2 independent actual visual0003 passes19.178s/three controls and both exact PNG '
    'visible-scope review; originals/source/owner guards saved. Eleven prepared test-only '
    'adjacent owner guards now applied using existing exact50 public baseline/no-follow checks, '
    'explicit scope/case wording; historical code/results unchanged and isolated policy payload '
    'walks retained. Product runtime source unchanged. Fresh matched debug0076/demo0077 '
    'builds and physical applicable readiness/query/source/diagnostic/UI/policy regressions '
    'required before F2 closure. No new regression/complete F2 acceptance from code writing. '
    'Mobile data on, PackRAG closed for background work; final owner packs excluded, F3/F4 held.')
target.write_text(json.dumps(dict(status='APPLIED_NOT_REGRESSION_ACCEPTED',recorded_utc=datetime.now(timezone.utc).isoformat(),visual_review_sha256=sha(review),preparation_sha256=sha(preparation),files=proposal['files'],note=note),indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    path=ROOT/name;header,rest=path.read_text(encoding='utf-8').split('\n',1)
    path.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print('APPLIED_ELEVEN_GUARD_ONLY_SOURCES_REQUIRE_MATCHED_REGRESSIONS')
