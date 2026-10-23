"""Freeze all-slot prerequisites and durable next action before phone source preparation."""
import hashlib,json,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
p=HERE/'all-slots-start-0001.json';assert not p.exists()
assert read(HERE/'restart-complete-0001.json')['status']=='PASS_F2_PROCESS_RECOVERY_ITERATION_NOT_FULL_F2'
capture=read(HERE/'build-0066-capture.json');assert capture['status']=='PASS_F2_API_ITERATION_HOST_APK_CONTRACTS_NOT_DEVICE_OR_F2_ACCEPTANCE'
old=read(M4/'build-0065/source-at-build-start.json')['files'];new=read(M4/'build-0066/source-at-build-start.json')['files']
delta={name:dict(before=old.get(name),after=value) for name,value in new.items() if old.get(name)!=value}
assert set(delta)=={'product/android/app/src/androidTest/java/org/packrag/product/AssetFixtureProvider.java',
    'product/android/app/src/androidTest/java/org/packrag/product/AssetFixtureGrantReceiver.java',
    'product/android/app/src/androidTest/java/org/packrag/product/LocalAssetImportAllSlotsDeviceTest.kt',
    'product/android/app/src/androidTest/assets/asset-import-source/owner-public-baseline.json'}
assert sha(M4/'build-0065/app-debug.apk')==sha(M4/'build-0066/app-debug.apk')
with zipfile.ZipFile(M4/'build-0066/app-debug-androidTest.apk') as z:
    baseline=json.loads(z.read('assets/asset-import-source/owner-public-baseline.json'))
    assert baseline==read(HERE/'before.json')['owner_public_file_sha256'] and len(baseline)==50
t=datetime.now(timezone.utc).isoformat()
note=f'Current M4F2 full-size four-slot iteration START at {t}: actual importing-process recovery0065 passed3 checkpoints and originals/known50 guards saved. Build0066 passes73 host methods/{len(new)} frozen inputs/APK contracts; only2 test provider/grant sources plus new all-slot test and explicit known50 public-baseline asset change. Product APK is byte-identical0065/66; no product privileges/model pins/runtime change. Test provider exposes only4 fixed read-only routes backed by exact owned-marker/no-follow/expected-size source files under newly created test-UID files/f2-full-assets-0001. Rootless on-device pipefail-checked copies from4 known owner model paths, no host weight export, verify whole source SHA before/after; source preparation asserts free space for2 full sets+64MiB, unknown namespace causes stop. New production-API test starts with no model destination, imports each actual1593894944/5443/25301672/390004608bytes through separate-UID narrow grants, records monotonic observed bytes/stages/time and one descriptor open/close, independently hashes final files, verifies all4, then runs cold and warm real cited synthetic answers. Owner guard reads/hash only50 explicitly named public files without custody traversal. Source set deliberately retained and explicitly validated for later approved-policy/UI reuse; only isolated owned destination removed after native close. Actual device/source prep results pending, not full F2 acceptance. Next source preparation then all-slot actual test, original evidence/custody before later UI. System picker/ViewModel/UI/approved-policy/regressions/restoration/closure remain; no F3/full M4/product/release claim. Mobile data stays on and PackRAG closed; final knowledge packs owner supplied.'
record=dict(status='F2_ALL_SLOT_ITERATION_STARTING_NOT_ACCEPTED',recorded_utc=t,source_delta=delta,unchanged_product_sha256=sha(M4/'build-0066/app-debug.apk'),host_capture_sha256=sha(HERE/'build-0066-capture.json'),note=note)
p.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    path=ROOT/name;header,rest=path.read_text(encoding='utf-8').split('\n',1);path.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(record['status'])
