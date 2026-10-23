"""Require observable query dispatch before accepting the new completion; preserve failed UI3."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
target=HERE/'ui-submission-sync-preparation-0001.json';driver=HERE/'run_picker_ui_submission.py';assert not target.exists() and not driver.exists()
run=M4/'device-local-asset-import-ui-0003';execution=HERE/'device-local-asset-import-ui-0003-execution.json';assert read(execution)['status']=='FAIL'
raw=run/'failure-original-adb/m4-local-asset-import-ui-progress.json';device=read(raw)
assert device['status']=='FAIL' and len(device['cases'])==6 and device['current_point']=='ACTUAL_POST_IMPORT_UI_QUERY'
recreation=device['pending_picker_recreation'];assert recreation['requested_lifecycle_state']=='CREATED'
for key in ['previous_activity_destroyed','distinct_activity_created','saved_state_bundle_present','same_viewmodel','picker_still_foreground']:assert recreation[key] is True
assert 'Values should be different' in (run/'instrumentation.txt').read_text(encoding='utf-8')
assert read(HERE/'ui-failed-0003-after-known-guard.json')['status']=='PASS_KNOWN50_EXISTING_PUBLIC_FILES_UNCHANGED'
old=read(M4/'build-0072/source-at-build-start.json')['files'];changed={name:sha(ROOT/name) for name,value in old.items() if sha(ROOT/name)!=value}
assert set(changed)=={'product/android/app/src/androidTest/java/org/packrag/product/LocalAssetImportUiDeviceTest.kt'}
text=(HERE/'run_picker_ui_recreation.py').read_text(encoding='utf-8').replace("'build-0072'","'build-0073'")
needle="    audit = device['actual_system_document_open']";assert text.count(needle)==1
text=text.replace(needle,"    assert device['new_query_dispatch_observed'] is True\n"+needle);driver.write_text(text,encoding='utf-8')
pngs={}
for name in ['m4-local-asset-import-ui-progress.png','m4-local-asset-import-ui-verified.png']:
    p=run/'failure-original-adb'/name;assert p.read_bytes().startswith(b'\x89PNG\r\n\x1a\n');pngs[name]=sha(p)
note=('UI0003 terminal FAIL156.632s at unchanged completion UUID after attempted GUI submission. Six recorded actual controls pass, including destroyed stopped caller/distinct recreated Activity with saved bundle/same ViewModel/system picker foreground, exact selected official-template grant/install and canonical-source/back navigation. Two actual partial-run PNGs preserved; not full acceptance. Old answer retained at final check; dispatch/busy timing was not recorded, so missed touch versus synchronization remains unresolved, not a product-generation failure conclusion. Single test-source repair now checks entered question/date and enabled button, waits for Compose idle before tap, requires observed busy or changed/cleared completion within10s before waiting for final answer, and persists dispatch observation. Final new-ID/cold native/canonical/citation assertions unchanged; no automatic button retry or substituted generation.597 other inputs unchanged/product sources untouched; build0073 pending and whole product APK equality required. Owner50 unchanged after failure. New original/versioned driver prepared; current foreground window must be renewed if exhausted. Approved-policy0070 retained, full F2/F3/F4 not accepted.')
record=dict(status='PREPARED_QUERY_SUBMISSION_SYNC_NOT_RETRY_OR_F2_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),execution_sha256=sha(execution),progress_sha256=sha(raw),partial_run_png_sha256=pngs,changed_test_source=changed,unchanged_inputs=597,driver_sha256=sha(driver),note=note)
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as s:s.write('\n\n'+note+'\n')
print(record['status'])
