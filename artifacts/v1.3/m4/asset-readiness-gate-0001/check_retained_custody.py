"""Explicit public-whitelist custody check during F1; no new regression execution claim."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
target=HERE/'retained-custody-0001.json';assert not target.exists()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
blocked={'.private','temp','stage','runner-temp','host-temp','pytest-temp'}
forbidden={'.seed','.seed32','.key','.keystore','.jks','.pem'}
def verify(mapping):
    for name,value in mapping.items():
        p=ROOT/name
        assert not blocked.intersection(part.lower() for part in Path(name).parts) and p.suffix.lower() not in forbidden,name
        assert p.resolve().is_relative_to(ROOT) and not p.is_symlink() and sha(p)==value,name
e3_path=M4/'diagnostics-gate-0001/gate.json';e3=read(e3_path)
assert sha(e3_path)=='683272dc411f8065ea8fc8811475f74348ab741a9b7f0c726524bea14f5ed702'
assert len(e3['source_sha256'])==188;verify(e3['source_sha256']);verify(e3['output_sha256'])
history_path=ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json';history=read(history_path)['files'];assert len(history)==587;verify(history)
current=read(M4/'build-0056/source-at-build-start.json')['files'];assert len(current)==579
assert current==read(M4/'build-0057/source-at-build-start.json')['files'];verify(current)
record=dict(status='PASS_RETAINED_PUBLIC_CUSTODY_AND_SOURCE_IDENTITY_NOT_FRESH_TEST_RUN_OR_F1_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    prior_e3_gate_sha256=sha(e3_path),prior_e3_public_outputs_unchanged=len(e3['output_sha256']),historical_guard_sha256=sha(history_path),historical_public_files_unchanged=587,
    retained_python_tests=1034,unchanged_python_runtime_inputs=188,current_android_inputs=579,
    scope='Exact independently pre-existing public SHA whitelists, private custody excluded before access. E3 results and old failures unchanged. Retained1034 Python and prior desktop gates are not newly executed at F1. Actual current F1 host/device/UI/policy tests and final closure remain separate; fresh full regression required at F4.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status']);print('Prior E3 outputs',len(e3['output_sha256']),'historical',len(history),'runtime188 Android579')
