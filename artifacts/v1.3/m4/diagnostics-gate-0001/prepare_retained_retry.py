"""Same APK/class/assertions after completed failed run, fresh owner reply and results."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert read(HERE/'retained-ui-execution.json')['status']=='FAIL'
run=M4/'device-ui-diagnostics-retained-0001';partial=read(run/'partial-collected-results.json')
assert partial['status']=='SAVED_TWO_COMPLETED_PASSING_METHODS_OVERALL_FOUR_METHOD_SUITE_FAIL'
for n,v in partial['original_sha256'].items():assert sha(run/'original-adb'/n)==v
sources=read(M4/'build-0048/source-at-build-start.json')['files']
for n,v in sources.items():assert sha(ROOT/n)==v,n
original=HERE/'run_retained_ui.py';source=original.read_text(encoding='utf-8')
changes=[('device-ui-diagnostics-retained-0001','device-ui-diagnostics-retained-0002'),
    ('foreground-retained-readiness.json','foreground-retained-retry-readiness.json'),
    ("['owner_quote']=='GO AHEAD ILL LEAVE THE PHONE UNTOUCHED'","['owner_quote']=='Yes, retry after this run finishes; I will leave it untouched'"),
    ('retained-ui-execution.json','retained-ui-retry-execution.json'),('retained-ui-stage-','retained-ui-retry-stage-')]
for before,after in changes:
    assert source.count(before)>=1,before;source=source.replace(before,after)
target=HERE/'run_retained_ui_retry.py';assert not target.exists();target.write_text(source,encoding='utf-8')
ready=HERE/'record_foreground_retained.py';value=ready.read_text(encoding='utf-8')
value=value.replace('foreground-retained-readiness.json','foreground-retained-retry-readiness.json').replace('GO AHEAD ILL LEAVE THE PHONE UNTOUCHED','Yes, retry after this run finishes; I will leave it untouched')
value=value.replace('Latest human message in this active continuation; no new reply is invented.','Actual human async reply to question call_c24b849a9d95488f83378a9642057229, received after foreground interruption; no new reply is invented.')
target=HERE/'record_foreground_retained_retry.py';assert not target.exists();target.write_text(value,encoding='utf-8')
visual=HERE/'record_retained_visual.py';v=visual.read_text(encoding='utf-8').replace('device-ui-diagnostics-retained-0001','device-ui-diagnostics-retained-0002').replace('retained-ui-execution.json','retained-ui-retry-execution.json')
target=HERE/'record_retained_visual_retry.py';assert not target.exists();target.write_text(v,encoding='utf-8')
target=HERE/'retained-ui-retry-preparation.json';assert not target.exists();target.write_text(json.dumps(dict(status='PREPARED_SAME_SOURCE_APK_UI_RETRY_NOT_EXECUTION',
    original_driver_sha256=sha(original),derived_driver_sha256=sha(HERE/'run_retained_ui_retry.py'),replacements=changes,
    apk_sha256={p.name:sha(p) for p in (M4/'build-0048').glob('*.apk')},unchanged_android_inputs=len(sources),
    partial_failed_run_originals=partial['original_sha256'],scope='No test/class/timeout/variant or production change. New untouched readiness/window, fresh execution/originals/PNG/visual required; old four-method suite remains FAIL.'),indent=2)+'\n',encoding='utf-8')
print('PASS same574 inputs/APKs and saved partial originals; fresh retry prepared')
