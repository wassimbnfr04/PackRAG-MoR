"""Preserve failing branch labels and bind exact test-only descriptor dispatch correction."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'cancel-harness-repair-0001.json';assert not target.exists()
partial=read(HERE/'fault-partial-0001.json');assert partial['status'].startswith('OVERALL_FAIL')
old=read(M4/'build-0062/source-at-build-start.json')['files'];new=read(M4/'build-0063/source-at-build-start.json')['files']
delta={n:dict(before=old.get(n),after=v) for n,v in new.items() if old.get(n)!=v}
assert set(old)==set(new) and set(delta)=={'product/android/app/src/androidTest/java/org/packrag/product/AssetFixtureProvider.java',
    'product/android/app/src/androidTest/java/org/packrag/product/LocalAssetImportFaultDeviceTest.kt'}
assert sha(M4/'build-0062/app-debug.apk')==sha(M4/'build-0063/app-debug.apk')
time=datetime.now(timezone.utc).isoformat()
record=dict(status='TEST_HARNESS_DISPATCH_REPAIR_PREPARED_NOT_PHYSICAL_CANCEL_ACCEPTANCE',recorded_utc=time,source_delta=delta,
    unchanged_product_sha256=sha(M4/'build-0063/app-debug.apk'),host_capture_sha256=sha(HERE/'build-0063-capture.json'),
    public_api_basis='Android ContentResolver read-mode content URI opens a typed */* descriptor. ContentProvider default typed implementation calls the two-argument openAssetFile. Explicit typed-cancellable/noncancellable/asset overrides now route each fixture to its intended handler; regular fallback is direct descriptor construction, without virtual-call recursion.',
    references=['https://developer.android.com/reference/android/content/ContentResolver','https://developer.android.com/reference/android/content/ContentProvider'],
    limits='First failed method only establishes future already done, not its result/cause, because no byte/result trace was saved. Earlier25 passing assertions are preserved but short-pipe label alone does NOT establish a physical pipe: old typed default can serve the regular fallback. That first assertion is not accepted as pipe-transport evidence. No rejected input/path assertion or original output is rewritten.',
    correction='Test-only counters now record typed-cancellable/plain/pipe dispatch; cancellation test requires partial observed bytes1..5442 and exact counter increments, then unfinished future. Cooperative blocked pipe leaves500ms between bounded valid writes, so a closed reader is detected by the next write even if the open-time signal transport is detached. Opening cancellation separately tests actual transported signal. Record explicit byte/ms labels and verify timings only for the two *_ms keys; bytes are not interpreted as milliseconds.',
    next='Fresh0063 faults0002 then native walking0003 in serial; halt on failure, collect originals before later work. No startup/process-death/all-slot/UI or F2 acceptance is advanced by this prepared repair.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
note=f'Current F2 harness retry at {time}: fault0001 remainsFAIL;25 actually passing assertions/two originals preserved, but its short-pipe label is not physical pipe proof because old typed fallback can serve a regular file. '+record['public_api_basis']+' '+record['correction']+' Build0063 passes73 host/APK contracts; only two test sources change vs0062 and product APK is byte-identical. Fresh faults0002/native0003 serial sequence starts, no actual new PASS yet. All known50 owner hashes match after failed0001; no app permission/root/radio changes. Hold restart/all-slot/UI/F3 until repaired iteration and real native regression pass.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(record['status'],flush=True)
