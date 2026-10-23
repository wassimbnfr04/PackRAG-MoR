"""Durable partial F2 hardening state before actual phone acceptance."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'hardening-start-0001.json';assert not target.exists()
walking=read(M4/'device-local-asset-import-walking-0002/execution.json');assert walking['status']=='PASS'
old=read(M4/'build-0061/source-at-build-start.json')['files'];new=read(M4/'build-0062/source-at-build-start.json')['files']
delta={n:dict(before=old.get(n),after=v) for n,v in new.items() if old.get(n)!=v}
assert set(delta)=={'product/android/app/src/main/java/org/packrag/product/LocalAssetImporter.kt','product/android/app/src/androidTest/java/org/packrag/product/LocalAssetImportFaultDeviceTest.kt'}
host=read(HERE/'build-0062-capture.json');assert host['host_xml_totals']==dict(tests=73,failures=0,errors=0,skipped=0)
time=datetime.now(timezone.utc).isoformat()
note=f'Current M4F2 hardening at {time}: API walking0002 on0060 PASS seven actual controls/354.105 whole-instrumentation seconds. Actual separate-UID provider opens1/closes1/errors0,5443 bytes/pin/directory sync, foreign warm reader rejection before input, caller native close and real cold answers before/after both74°C[S1],153 emitted tokens,15.150470508/14.037141054s initialization (functional observations, not M8 benchmark). Original JSON bytes saved and known50 owner hashes match; F1 outputs406/history587/Python188 remain unchanged. Hardening adds validated owned startup reconciliation, bounded/no-follow marker read, new-parent directory sync, explicit staging-cleanup confirmation/failure pending flag, independent idempotent per-operation close/cancellation workers and sanitized final source cleanup. New real-URI grant/revoke/empty/short/oversized/corrupt/wrong-slot/metadata-lie/cooperative-pipe/opening cancellation and Android symlink/recovery/fault tests are prepared, not yet passed. Build0061 host73 passes but review finds finally could inspect through a rejected symlinked root; it is not executed on the phone and not promoted to transport/security acceptance. Exact source/APKs are preserved. Corrected0062 revalidates root/ancestors/owned namespace before any cleanup inspection and tests an existing valid stage behind the rejected root alias; only importer and one test source change vs0061. Build0062 passes73 host methods (62 retained +11 importer contracts),{host["android_inputs"]} inputs/APK/public trust/native/no-INTERNET contracts. Actual three-method/28-control fault suite then fresh seven-control native walking0003 start serially; stop sequence on any failure and save originals before subsequent work. This is not F2 completion. All-four-artifact import, actual process-death, ViewModel/system-picker/progress/cancel UI, matched approved-only/adjacent/F1 regressions, restoration/custody/closure/exact checkpoint remain before F3. F3/F4/later software/release/delivery remain; owner supplies final packs, mobile data stays on and PackRAG remains closed during background checks.'
record=dict(status='F2_HARDENING_TESTS_STARTING_NOT_ACCEPTED',recorded_utc=time,walking_iteration_sha256=sha(M4/'device-local-asset-import-walking-0002/execution.json'),
    predevice_cleanup_review='Static review of0061, no device corruption or completed physical failure claimed. RootSafe gate and fresh ancestor/namespace no-follow validation added to finally before child inspection; regression preserves existing known stage through a rejected symlink alias.',
    source_delta_0061_to_0062=delta,host_capture_sha256=sha(HERE/'build-0062-capture.json'),note=note)
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(record['status'],flush=True)
