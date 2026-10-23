"""Independent exact-image visual review after successful physical collection."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
run=ROOT/'artifacts/v1.3/m4/device-local-asset-import-visual-0003'
target=HERE/'visual-inspection-visual0003.json';assert not target.exists()
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
execution=json.loads((HERE/'device-local-asset-import-visual-0003-execution.json').read_text())
assert execution['status']=='PASS_F2_SEPARATE_PICKER_STATIC_FRAME_CONTRACTS_MANUAL_VISUAL_REVIEW_PENDING'
device=json.loads((run/'original-adb/m4-local-asset-import-visual.json').read_text())
review={
    'm4-local-asset-import-visual-progress.png':{
        'visible':'Full1080px product width, header/system bars, actual Copying256/5443bytes, progress indicator, Cancel import enabled, Check local files/chooser disabled during copy. Guidance and generator pin wrap normally; template heading/expected5443bytes visible. No lateral picker exit surface or translated/cropped product width.',
        'limits':'Scrolled viewport; template hash/check fields below bottom are not covered by this image. Raster displays256bytes while near-sample ViewModel observations record512bytes: independently sampled rendered/state values, not a synchronized counter/latency/performance assertion.'},
    'm4-local-asset-import-visual-verified.png':{
        'visible':'Full1080px product width, installed-and-verified message, enabled check/generator chooser, template exact-size/SHA256-match last-check guidance, expected/observed5443bytes, entire wrapped expected template SHA256. Generator still configured/unchecked as required in template-only isolated root. No lateral picker surface/text crop.',
        'limits':'Scrolled viewport; top introductory sentence and bottom check timestamp cross viewport boundaries normally. No assertion for offscreen other slots, their readiness, complete timestamp legibility, native generation or all-four-ready in this visual-only run.'}}
for name,value in review.items():
    value.update(status='PASS_VISIBLE_SCOPE',sha256=sha(run/'original-adb'/name))
    assert value['sha256']==device['visual_png'][name]['sha256']==execution['png_sha256'][name]
note=('Separate visual0003 actual JUnit1/three controls PASSED19.178s; original main/progress '
    'and two unmodified1080x2316 PNGs saved/hash-bound before switch. Independent view_image '
    'review passes readable full-width visible progress/cancel/verified-template fields; normal '
    'scroll clipping and raster256bytes versus separately sampled state512bytes documented, '
    'not full-screen content coverage or synchronized progress/performance proof. Exact599 '
    'inputs unchanged during execution; all598 UI0004 sources and whole product APK identical. '
    'Retained UI0004 actual eight controls/cold153token validated74°C[S1] result remains '
    'separately dated, its original visual FAIL unchanged; no relabelled new native experiment. '
    'Visual0001 install timeout/visual0002 PACKAGE UPDATED interruption remain FAIL; owner '
    'confirmed Ne pas envoyer and new4min foreground window, now ended. Known50/source4 '
    'unchanged. Next apply prepared eleven guard-only proposals, fresh matched debug/demo '
    'builds and relevant actual adjacent regressions, then restoration/custody/closure/exact '
    'checkpoint before F3. Full F2/M4/product not complete; final owner packs excluded/mobile data on.')
target.write_text(json.dumps(dict(status='PASS_VISUAL_SEPARATE_PICKER_TEMPLATE_SCOPE_NOT_FULL_F2',recorded_utc=datetime.now(timezone.utc).isoformat(),test_id=device['test_id'],reviews=review,execution_sha256=sha(HERE/'device-local-asset-import-visual-0003-execution.json'),unchanged_ui4_inputs=execution['unchanged_ui4_inputs'],note=note),indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    path=ROOT/name;header,rest=path.read_text(encoding='utf-8').split('\n',1)
    path.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md','docs/v1.3/M4F2_SYSTEM_PICKER_METHODS.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print('PASS_VISUAL_SEPARATE_PICKER_TEMPLATE_SCOPE_NOT_FULL_F2')
