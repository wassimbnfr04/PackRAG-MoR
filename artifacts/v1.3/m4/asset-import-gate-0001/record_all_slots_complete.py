"""Durable all-slot iteration evidence; explicit remaining ViewModel/system-picker gates."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
target=HERE/'all-slots-complete-0001.json';assert not target.exists()
name='device-local-asset-import-all-slots-0001';execution=HERE/(name+'-execution.json');result=read(execution)
assert result['status']=='PASS_F2_ACTUAL_ALL_FOUR_FULL_SIZE_URI_IMPORT_AND_COLD_WARM_NATIVE_NOT_UI_OR_FULL_F2'
raw=M4/name/'original-adb/m4-local-asset-import-all-slots.json';device=read(raw);assert sha(raw)==result['original_sha256'][raw.name]
assert device['status']=='PASS' and len(device['cases'])==8
time=datetime.now(timezone.utc).isoformat()
note=f'Current M4F2 full-size four-slot API/native iteration PASSED at {time}: build0066 passes73 host/{read(HERE/"build-0066-capture.json")["android_inputs"]} frozen inputs/contracts, actual all-slots0001 passes8 ordered controls. Total2009206667 bytes imported via actual separate-UID read descriptors into initially absent isolated private model destination; generator/template/tokenizer/encoder exact pins verified by importer readback and independent final verification. All4 actual descriptor opens/closes/typed-cancellable calls counted once each, no close errors/plain typed calls. Monotonic actual byte counts/stage order/callback counts/import duration persisted; durations are functional observations, not controlled performance acceptance. Cold and warm real synthetic74°C[S1] answers pass retrieval/admission/selection/LFM2.5/reasoning removal/citation checks with actual tokens/native context. Original main/progress JSON saved/hash-bound before any switch; explicit owner50 and four test-UID source full hashes match before/after. Newly owned source copies stayed on phone (no host weight export) and deliberately remain readonly for identified later policy/UI reuse; owned destination cleaned after native close. Accepted F1 outputs406/history587/Python188 identities unchanged in independent restart-and-all-slot-retained-custody0001 (retained evidence, not a fresh whole regression run). Product APK unchanged0065/66; only test harness sources/public baseline asset changed. Next F2 iteration: wire real fixed-slot OpenDocument picker, ViewModel serialized import/progress/cooperative cancellation, preserve completed answer/trace/submission/resultID on success/failure/picker cancel; actual ViewModel/native tests then system-picker/foreground UI with fresh announced untouched window. Approved-policy matched-source tests, retained regressions/restoration/custody/closure/exact checkpoint remain. F3/F4/later software/release/delivery remain; no full F2/M4/product/release/power-loss/domain/gold/performance claim. Mobile data on; background PackRAG closed; final knowledge packs owner supplied.'
record=dict(status='PASS_F2_ALL_SLOT_API_NATIVE_ITERATION_NOT_FULL_F2',recorded_utc=time,execution_sha256=sha(execution),original_sha256=result['original_sha256'],imports=device['imports'],note=note)
target.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as s:s.write('\n\n'+note+'\n')
print(record['status'])
