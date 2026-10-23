"""Record actual background ViewModel evidence before further picker/UI source changes."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
target=HERE/'viewmodel-complete-0001.json';assert not target.exists()
name='device-local-asset-import-viewmodel-0001';execution=HERE/(name+'-execution.json');result=read(execution)
assert result['status']=='PASS_F2_BACKGROUND_PRODUCTION_VIEWMODEL_IMPORT_PRESERVATION_CANCEL_AND_NATIVE_NOT_PICKER_UI_OR_FULL_F2'
raw=M4/name/'original-adb/m4-local-asset-import-viewmodel.json';device=read(raw);assert sha(raw)==result['original_sha256'][raw.name]
assert device['status']=='PASS' and len(device['cases'])==8
time=datetime.now(timezone.utc).isoformat()
note=f'Current M4F2 background production ViewModel/native iteration PASSED at {time}:0067 host73/frozen595/contracts and actual ViewModel0001 passed8 controls in311.509 whole-instrumentation seconds. Actual first completed accepted synthetic74°C[S1] answer/trace/submission/resultID survived wrong-hash rejection, generic non-content-URI recovery, observed128byte partial-copy read cancellation, transported opening cancellation, successful verified template import and independent four-file recheck with identical object references/completion UUID. Cancel dispatch measured {device["reading_cancel_dispatch_ms"]}ms read / {device["opening_cancel_dispatch_ms"]}ms opening; completion15s watchdogs passed for cooperative test provider, not arbitrary IPC/performance bounds. New post-import cold real JNI accepted answer passed required initialization/canonical source/reasoning removal/citations and new completion UUID. Main/progress originals saved/hash-bound before any source/APK change; exact known owner50 and retained readonly test-UID source4 hashes unchanged. Test-only Application storage override and owned-root cleanup used; product storage paths/pins/native/trust/permissions unchanged. Actual system-picker callback/cancel/saveable slot, Activity/progress/control/back/source UI/visual inspection not yet validated; these are next, requiring a prepared separate test and fresh announced untouched window. Approved-policy/matched-source and retained regressions/restoration/custody/closure/checkpoint remain before F3, then F3 presentation/accessibility and F4 comprehensive M4 gates. Earlier M4 stages are complete; F1-F4 are finishing stages, not the entire M4 decomposition. Full F2/M4/product/release/domain/gold/performance acceptance not declared. Final knowledge packs owner supplied; mobile data on; keep PackRAG closed during background tests.'
record=dict(status='PASS_F2_BACKGROUND_VIEWMODEL_ITERATION_NOT_FULL_F2',recorded_utc=time,execution_sha256=sha(execution),original_sha256=result['original_sha256'],note=note)
target.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as s:s.write('\n\n'+note+'\n')
print(record['status'])
