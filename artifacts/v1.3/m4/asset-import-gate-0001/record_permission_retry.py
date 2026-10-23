"""Bind observed failed transport setup and the one test-only retry change."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'permission-retry-0001.json';assert not target.exists()
failed=M4/'device-local-asset-import-walking-0001';execution=read(failed/'execution.json');assert execution['status']=='FAIL'
raw=(failed/'instrumentation.txt').read_text(encoding='utf-8')
assert 'SecurityException' in raw and 'not exported from UID 10472' in raw and 'uid=10469' in raw and 'Time: 14,479' in raw
assert any('NARROW_TEMPLATE_READ_GRANTED' in command['stdout'] and 'result=1' in command['stdout'] for command in execution['commands'])
old=read(M4/'build-0059/source-at-build-start.json')['files'];new=read(M4/'build-0060/source-at-build-start.json')['files']
delta={n:dict(before=old.get(n),after=v) for n,v in new.items() if old.get(n)!=v}
assert set(old)==set(new) and set(delta)=={'product/android/app/src/androidTest/java/org/packrag/product/LocalAssetImportWalkingDeviceTest.kt'}
assert sha(M4/'build-0059/app-debug.apk')==sha(M4/'build-0060/app-debug.apk')
guard=read(HERE/'failed-walking-0001-after-guard.json');assert guard['status']=='PASS_KNOWN50_EXISTING_PUBLIC_FILES_UNCHANGED'
record=dict(status='PASS_FAILURE_CUSTODY_AND_TEST_ONLY_RETRY_BINDING_NOT_NATIVE_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    original_failure_sha256={name:sha(failed/name) for name in ['instrumentation.txt','execution.json','instrumentation-manifest.json','failure.txt']},
    observed_failure='First provider audit query denied before pre-import native query/import. Earlier actual receiver broadcast returned result1. Actual target/provider UIDs10469/10472 differ. Instrumentation whole-test time14.479s, not performance metric.',
    root_cause_limit='Pre-instrumentation grant was insufficient at actual provider acquisition. Instrumentation setup revoking that grant is a hypothesis; no captured platform grant-lifecycle trace establishes its cause.',
    correction='Only the instrumentation walking test now requests the same DUMP-protected explicit narrow read grant through actual UiAutomation shell broadcast after instrumentation starts. No adopted permission/product privilege/root/radio changes. Assert actual broadcast result before provider query. Real successful retry is required; none claimed here.',
    source_delta=delta,unchanged_debug_product_sha256=sha(M4/'build-0060/app-debug.apk'),known50_postfailure_guard_sha256=sha(HERE/'failed-walking-0001-after-guard.json'),
    retry='device-local-asset-import-walking-0002',scope='Failed0001 staysFAIL, no structured native/URI PASS original exists for it. All F2 hardening/UI progression held until corrected walking iteration passes; F2/F3/F4/later gates remain.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
note=f'F2 permission setup retry at {record["recorded_utc"]}: '+record['observed_failure']+' '+record['root_cause_limit']+' '+record['correction']+' All known50 public owner-file hashes match after the failed run; failed original outputs remain immutable. New0060 product APK is byte-identical to0059; only one walking instrumentation source changes, all original answer/import assertions remain. Retry0002 is running; not native acceptance yet.'
for name in ['docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md','DECISIONS.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(record['status'],flush=True)
