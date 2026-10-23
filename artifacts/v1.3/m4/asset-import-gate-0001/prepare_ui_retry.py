"""Preserve failed UI scope and produce a readable retry driver for the single harness repair."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
target=HERE/'ui-assertion-repair-preparation-0001.json';driver=HERE/'run_picker_ui_retry.py';assert not target.exists() and not driver.exists()
failure=M4/'device-local-asset-import-ui-0001'
execution=HERE/'device-local-asset-import-ui-0001-execution.json';assert read(execution)['status']=='FAIL'
old=read(M4/'build-0069/source-at-build-start.json')['files']
changed={name:sha(ROOT/name) for name,value in old.items() if sha(ROOT/name)!=value}
ui='product/android/app/src/androidTest/java/org/packrag/product/LocalAssetImportUiDeviceTest.kt'
assert set(changed)=={ui}
old_ui=HERE/'build-0069-tested-sources'/ui
expected=old_ui.read_text(encoding='utf-8').replace('assertTextContains("rejected")','assertTextContains("rejected",substring=true)').replace('assertTextContains("5443 bytes")','assertTextContains("5443 bytes",substring=true)').replace('assertTextContains("Exact size and SHA256")','assertTextContains("Exact size and SHA256",substring=true)')
assert (ROOT/ui).read_text(encoding='utf-8')==expected
captured={}
for name in ['m4-local-asset-import-ui.json','m4-local-asset-import-ui-progress.json','m4-local-asset-import-ui-progress.png','m4-local-asset-import-ui-verified.png']:
    path=failure/'failure-original-adb'/name;payload=path.read_bytes();entry=dict(sha256=sha(path),bytes=len(payload))
    if name.endswith('.json'):
        try:
            value=json.loads(payload);entry.update(format='JSON',status=value.get('status'),test_id=value.get('test_id'),current_point=value.get('current_point'))
        except (ValueError,UnicodeError):entry.update(format='NOT_JSON_COMMAND_OUTPUT_NO_RESULT_ACCEPTANCE',command_output_utf8=payload.decode('utf-8',errors='replace'))
    else:entry['format']='PNG_UNACCEPTED' if payload.startswith(b'\x89PNG\r\n\x1a\n') else 'NOT_PNG_COMMAND_OUTPUT_NO_SCREENSHOT_ACCEPTANCE'
    captured[name]=entry
assert captured['m4-local-asset-import-ui-progress.json']['status']=='FAIL'
text=(HERE/'run_picker_ui.py').read_text(encoding='utf-8')
assert "'build-0069'" in text
driver.write_text(text.replace("'build-0069'","'build-0071'"),encoding='utf-8')
note=('First actual UI0001 terminal FAIL149.932s at corrupt-document displayed-message assertion. Frozen source and JUnit independently show correct LOCAL_ASSET_IMPORT_HASH_MISMATCH rejection and preserved file/completion assertions preceding failed exact-text comparison. Only two cases marked passed in actual progress; no later case/native/UI acceptance. Compose assertTextContains default did not accept substring; three intended fragment assertions now explicitly substring=true. Only one test source changed, all597 other inputs unchanged; product sources unchanged. Failed original captures include non-JSON/non-PNG cat error output for nonexistent files; those bytes remain preserved and never represent main results/screenshots. Current FAIL progress is valid JSON. Known50 after failure unchanged. Build0071 pending, exact product APK equality must be proven before retry. Fresh owner foreground authorization remains for the current announced window; extend only if needed. No F3 progression.')
record=dict(status='PREPARED_SINGLE_TEST_SUBSTRING_REPAIR_NOT_RETRY_OR_F2_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),execution_sha256=sha(execution),instrumentation_sha256=sha(failure/'instrumentation.txt'),changed_test_source=changed,unchanged_inputs=597,failure_captures=captured,retry_driver_sha256=sha(driver),note=note)
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as s:s.write('\n\n'+note+'\n')
print(record['status'])
