"""Prepare actual stopped-caller recreation test without changing production code or old evidence."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
target=HERE/'ui-recreation-repair-preparation-0001.json';driver=HERE/'run_picker_ui_recreation.py';assert not target.exists() and not driver.exists()
run=M4/'device-local-asset-import-ui-0002';execution=HERE/'device-local-asset-import-ui-0002-execution.json'
assert read(execution)['status']=='FAIL'
raw=run/'failure-original-adb/m4-local-asset-import-ui-progress.json';device=read(raw)
assert device['status']=='FAIL' and len(device['cases'])==4 and device['current_point']=='OFFICIAL_DOCUMENT_PENDING_RECREATION'
assert device['ui_observed_partial_copy_bytes']==128
assert 'Activity never becomes requested state' in (run/'instrumentation.txt').read_text(encoding='utf-8')
assert read(HERE/'ui-failed-0002-after-known-guard.json')['status']=='PASS_KNOWN50_EXISTING_PUBLIC_FILES_UNCHANGED'
old=read(M4/'build-0071/source-at-build-start.json')['files'];changed={name:sha(ROOT/name) for name,value in old.items() if sha(ROOT/name)!=value}
assert set(changed)=={'product/android/app/src/androidTest/java/org/packrag/product/LocalAssetImportUiDeviceTest.kt'}
text=(HERE/'run_picker_ui.py').read_text(encoding='utf-8').replace("'build-0069'","'build-0072'")
needle="    audit = device['actual_system_document_open']"
addition="    recreation = device['pending_picker_recreation']\n    assert recreation['requested_lifecycle_state'] == 'CREATED'\n    for field in ['previous_activity_destroyed', 'distinct_activity_created', 'saved_state_bundle_present', 'same_viewmodel', 'picker_still_foreground']:\n        assert recreation[field] is True\n"
assert text.count(needle)==1;text=text.replace(needle,addition+needle);driver.write_text(text,encoding='utf-8')
note=('UI0002 terminal FAIL189.619s after four recorded passing actual controls,128-byte displayed progress/cancel, owner50 unchanged. ActivityScenario.recreate() attempted to force the caller RESUMED while the actual Android picker correctly kept it STOPPED; frozen JUnit fails in the helper before actual recreation, no saveable-slot success claim. Replace only this test source with direct platform Activity.recreate() on the stopped caller and test-only Application lifecycle observation scoped to the unique launch UUID. Require real old destruction/distinct new Activity/saved bundle/same ViewModel/picker remaining foreground before selecting official document; persist all facts, never merely assume request implies recreation. Primary platform contract: https://developer.android.com/reference/android/app/Activity#recreate(). No product, global orientation/window/power/radio or permissions change. Original failed logs/partial progress PNG retained, not full acceptance. Build0072 pending; new driver strengthens structured recreation validation. Prior ten-minute foreground window ended; fresh window required when repaired test is concrete. Full F2/F3/F4 held.')
record=dict(status='PREPARED_STOPPED_CALLER_RECREATION_REPAIR_NOT_RETRY_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),execution_sha256=sha(execution),progress_sha256=sha(raw),instrumentation_sha256=sha(run/'instrumentation.txt'),changed_test_source=changed,unchanged_inputs=597,driver_sha256=sha(driver),note=note)
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as s:s.write('\n\n'+note+'\n')
print(record['status'])
