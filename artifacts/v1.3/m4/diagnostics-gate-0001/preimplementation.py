"""Verify the accepted E2 checkpoint before any E3 product edits."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    assert '.private' not in {part.lower() for part in p.resolve().parts}
    assert p.suffix.lower() not in {'.seed','.seed32','.pem','.key','.jks','.keystore'}
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(values):
    for name,value in values.items():
        path=ROOT/name;assert path.resolve().is_relative_to(ROOT),name
        assert sha(path)==value,name
target=HERE/'preimplementation.json';assert not target.exists()
old=M4/'source-details-gate-0001';gate=read(old/'gate.json')
assert gate['status']=='M4E2_CAPTURED_SOURCE_AND_VERIFIED_PACK_DETAILS_VERIFIED_NOT_COMPLETE_M4_OR_PRODUCT'
for field in ['source_sha256','android_source_sha256','output_sha256']:check(gate[field])
history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];check(history)
assert sha(ROOT/'FULL DOCUMENTATION.md')=='7c68e26003dc2debfbe4de9ce79467953fec5268c59947b93b2f2c01d612dbca'
assert sha(ROOT/'artifacts/v1.3/architecture/architecture-v1.3.docx')=='9b02f83b186a5b7f0101add861c6ecb40f5eb0b13016f50fa0c76efc6de07536'
library=old/'checkpoint_git.py';assert sha(library)==gate['output_sha256'][library.relative_to(ROOT).as_posix()]
spec=spec_from_file_location('accepted_e2_checkpoint_reader',library);module=module_from_spec(spec);spec.loader.exec_module(module)
commit=module.git('rev-parse','HEAD').stdout.decode().strip();assert commit=='b25ebfcf9dad3b340c92bacbcc1313bd0c479ffc'
assert module.git('branch','--show-current').stdout.decode().strip()=='codex/packrag-v1.3'
assert not module.git('diff','--cached','--name-only').stdout.strip()
manifest=old/'checkpoint-files.json';files=read(manifest)['files'];check(files)
files={**files,manifest.relative_to(ROOT).as_posix():sha(manifest)}
blobs=module.blobs('HEAD',sorted(files))
for name,value in files.items():assert blobs[name] is not None and hashlib.sha256(blobs[name]).hexdigest()==value,name
adb=ROOT/'vendor/platform-tools/adb.exe';device=subprocess.run([str(adb),'devices'],capture_output=True,check=True)
assert 'R3CT908DHHR\tdevice' in device.stdout.decode()
(HERE/'adb-devices.txt').write_bytes(device.stdout)
record=dict(status='PASS_E2_CHECKPOINT_SOURCE_EVIDENCE_HISTORY_PHONE_BEFORE_E3_NOT_E3_ACCEPTANCE',
    recorded_utc=datetime.now(timezone.utc).isoformat(),baseline_commit=commit,e2_gate_sha256=sha(old/'gate.json'),
    runtime_inputs=len(gate['source_sha256']),android_inputs=len(gate['android_source_sha256']),
    e2_public_outputs_unchanged=len(gate['output_sha256']),historical_unchanged=len(history),
    committed_whitelist_blobs=len(files),saved_final_original_results=gate['saved_final_original_results'],
    restored_build='build-0041',serial='R3CT908DHHR',mobile_data_preserved=True,
    statement='Read-only baseline verification precedes E3 implementation; owner final knowledge content stays outside agent authorship.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record))
