"""Record implementation and actual host validation; physical ViewModel/UI pending."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
target=HERE/'viewmodel-start-0001.json';assert not target.exists()
assert read(HERE/'all-slots-complete-0001.json')['status']=='PASS_F2_ALL_SLOT_API_NATIVE_ITERATION_NOT_FULL_F2'
host=read(HERE/'build-0067-capture.json');assert host['status']=='PASS_F2_API_ITERATION_HOST_APK_CONTRACTS_NOT_DEVICE_OR_F2_ACCEPTANCE'
old=read(M4/'build-0066/source-at-build-start.json')['files'];new=read(M4/'build-0067/source-at-build-start.json')['files']
delta={name:dict(before=old.get(name),after=value) for name,value in new.items() if old.get(name)!=value}
assert set(delta)=={'product/android/app/src/main/java/org/packrag/product/'+name+'.kt' for name in ['MainActivity','LocalAssetsScreen','PackRagViewModel']}|{'product/android/app/src/androidTest/java/org/packrag/product/'+name+'.kt' for name in ['LocalAssetImportTestSupport','LocalAssetImportViewModelDeviceTest']}
time=datetime.now(timezone.utc).isoformat()
note=f'Current M4F2 ViewModel/picker iteration START at {time}: actual four-slot0066 passed8 controls/cold+warm/native/originals/owner50/source4 guards, following earlier fault28/API7/process3 gates. Build0067 passes73 host/{len(new)} frozen Android inputs/APK/native/trust/no INTERNET contracts, actual app unit task executed; only3 product UI sources and2 new test sources change. Fixed-slot OpenDocument picker uses saveable primitive slot name; only a granted URI+valid slot dispatches to the production session API; picker cancellation dispatches no mutation, no URI reopening/persisted URI/arbitrary model destination/broad product storage privilege. Local-assets screen shows observed stage/bytes/progress, selected pinned-file chooser and cooperative cancel. Production ViewModel retains existing previous-job cancel/join+mutex serialization, epoch-filters cross-thread progress; cancellation marks request and cancels source/session without cancelling the action/pretending immediate rollback, waits for actual cleanup/commit, and observes the pre-session-ticket race at initial progress. Late commit may truthfully return installation. Existing preserveResult generic failure recovery now also preserves original answer/trace/submission/inputError/resultID (success already did), without carrying those results into ordinary pack mutation/new queries. Import typed rejection/cancel reports safe codes and pending-cleanup warnings; success reports verification and any postcommit sync/cleanup warning. Native-reader lease/security/correct pins unchanged. New background real ViewModel device test uses test-only Application filesDir/cacheDir isolation and known50 guards, sets up all4 real URI files and signed synthetic pack, makes actual accepted answer, verifies identical completion references across wrong-hash/generic-URI failure/128-byte blocked-read cancel/transported-open cancel/success/recheck, then actual new cold answer/new resultID. Device0001 is starting; physical ViewModel and actual picker/UI not yet PASS. Original evidence must be collected/known source+owner guards checked before source/APK switch; failure stops later UI. Actual system-picker selection/cancel/recreation/viewport/back/canonical-source regressions still need prepared test and fresh announced untouched window. Approved-policy/retained regressions/restoration/custody/closure/checkpoint still remain before F3, full M4/product/release not complete. Mobile data on; background PackRAG closed; owner final packs excluded.'
record=dict(status='F2_VIEWMODEL_PICKER_IMPLEMENTED_HOST_PASS_DEVICE_PENDING_NOT_ACCEPTED',recorded_utc=time,source_delta=delta,host_capture_sha256=sha(HERE/'build-0067-capture.json'),note=note)
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as s:s.write('\n\n'+note+'\n')
print(record['status'])
