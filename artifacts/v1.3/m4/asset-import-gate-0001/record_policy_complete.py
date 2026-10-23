"""Record completed physical approved-policy import/native evidence and current foreground phase."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
target=HERE/'policy-all-slots-complete-0001.json';assert not target.exists()
name='device-local-asset-import-all-slots-policy-0001';execution=HERE/(name+'-execution.json');value=read(execution)
assert value['status']=='PASS_F2_ACTUAL_ALL_FOUR_FULL_SIZE_URI_IMPORT_AND_COLD_WARM_NATIVE_NOT_UI_OR_FULL_F2'
assert value['build']=='build-0070'
raw=M4/name/'original-adb/m4-local-asset-import-all-slots.json';device=read(raw)
assert device['status']=='PASS' and device['variant']=='demo' and len(device['cases'])==8
for filename,digest in value['original_sha256'].items():assert sha(M4/name/'original-adb'/filename)==digest
assert read(HERE/(name+'-after-known-guard.json'))['status']=='PASS_KNOWN50_EXISTING_PUBLIC_FILES_UNCHANGED'
pair=HERE/'picker-policy-source-pair-0001.json';assert read(pair)['status']=='PASS_FROZEN_598_SOURCE_HOST_73_POLICY_PAIR_NOT_PHONE_OR_F2_ACCEPTANCE'
note=('M4F2 approved-only import/native iteration PASSED '+datetime.now(timezone.utc).isoformat()+': demo0070/debug0069 have identical598 frozen Android inputs,73 host methods each and identical native/public trust bytes. Actual policy all-slots0001 JUnit1 passes8 controls in234.251 whole-instrumentation seconds, importing all2009206667 bytes through actual separate-UID descriptors, exact pins/readback/atomic directory sync and cold/warm real cited74°C[S1] answers under approved-only signed calibration-schema fixture. This proves software policy, not genuine human calibration, domain/gold/performance or final nondebug release. Main/progress originals saved/hash-bound before restoring debug0069; known50 owner and readonly source4 unchanged. Owner explicitly authorized fresh10-minute untouched window; actual system-picker/UI0001 is RUNNING on frozen0069 under run_picker_ui.py. Do not kill/switch/compile/edit tested sources until terminal result and original JSON/PNG collection. Independent visible-scope PNG review and remaining adjacent regression guard repairs/matched final tests/restoration/custody/closure/checkpoint still required before F3/F4. F3 acceptance is prepared only, not implemented. Full F2/M4/product not declared; owner final packs excluded, mobile data on.')
record=dict(status='PASS_F2_PHYSICAL_APPROVED_POLICY_ALL_SLOT_NATIVE_ITERATION_NOT_FULL_F2',recorded_utc=datetime.now(timezone.utc).isoformat(),execution_sha256=sha(execution),pair_sha256=sha(pair),original_sha256=value['original_sha256'],note=note)
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
for filename in ['STATUS.md','PLAN.md']:
    p=ROOT/filename;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for filename in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/filename).open('a',encoding='utf-8') as s:s.write('\n\n'+note+'\n')
print(record['status'])
