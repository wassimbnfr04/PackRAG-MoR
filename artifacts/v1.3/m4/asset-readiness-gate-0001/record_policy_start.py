"""Record actual UI/visual completion and still-running policy sequence without closure."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'policy-start-0001.json';assert not target.exists()
execution=read(HERE/'policy-and-restoration-execution-0001.json');assert execution['status']=='RUNNING'
ui=M4/'device-local-assets-ui-0001';assert read(ui/'instrumentation-manifest.json')['status']=='PASS'
visual=read(HERE/'ui-visual-0001.json');assert visual['status']=='PASS_F1_ORIGINAL_ASSET_SCREEN_TESTED_VIEWPORT'
text=(ui/'instrumentation.txt').read_text(encoding='utf-8');assert 'OK (1 test)' in text and 'FAILURES' not in text
match=re.search(r'Time:\s*([0-9][0-9\s\u00a0\u202f]*[.,][0-9]+)',text);assert match
seconds=float(re.sub(r'\s','',match[1]).replace(',','.'))
record=dict(status='RUNNING_POLICY_AFTER_ACTUAL_UI_VISUAL_PASS_NOT_F1_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    ui_methods=1,ui_controls=5,ui_whole_instrumentation_seconds=seconds,ui_visual_sha256=sha(HERE/'ui-visual-0001.json'),
    policy_sequence_started_utc=execution['started_utc'],foreground_window_over=True,
    scope='Actual real-file/recreation/question/owned-answer/source navigation UI and original report/two PNGs pass. Manual review names exact visible fields and does not claim offscreen encoder size/hash/timestamp. Owner may use other apps/chat with USB/mobile data preserved; PackRAG closed during subsequent background guards. New approved-policy core/adjacent originals and restored development consent/final source/known50-file guards remain required. No F1 closure or F2 implementation.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
note=f'Current M4F1 at {record["recorded_utc"]}: local-assets UI0001 passes one method/five controls in {seconds} whole-instrumentation seconds. The actual question produces “The maximum continuous operating temperature of the Aster-9 is 74 °C [S1].” Original JSON and both exact1080×2316 PNGs are saved. Actual manual image inspection passes within explicitly recorded visible-field scope; encoder size/hash/timestamp below the second viewport are not claimed visually inspected. The roughly five-minute untouched window is over. Owner can use other apps/chat; keep PackRAG closed and USB/mobile data on. Approved-only0057 core then adjacent tests are RUNNING in the prepared serial sequence; all originals precede any APK switch, followed by restored0056 consent and final source/known50-file checks. Development core3, unchanged adjacent retry5 and UI1 are partial accepted scopes. Earlier hardlink/registry failures and whole-session default-registry preservation=false remain. F1 closure/exact checkpoint and F2/F3/F4/later software/release/delivery are still pending; owner supplies final knowledge content.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;head,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(head+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(record['status'])
