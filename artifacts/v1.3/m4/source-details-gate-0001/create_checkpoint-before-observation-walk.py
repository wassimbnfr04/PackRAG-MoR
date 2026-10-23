"""After E2 closure: tested delta, exact public evidence and durable documents."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def merge(left,right):
    assert all(left[k]==right[k] for k in left.keys() & right.keys())
    return {**left,**right}
gate=read(HERE/'gate.json');assert gate['status']=='M4E2_CAPTURED_SOURCE_AND_VERIFIED_PACK_DETAILS_VERIFIED_NOT_COMPLETE_M4_OR_PRODUCT'
prior=read(M4/'ui-query-gate-0002/gate.json')
baseline=merge(prior['source_sha256'],prior['android_source_sha256'])
current=merge(gate['source_sha256'],gate['android_source_sha256'])
assert not baseline.keys()-current.keys(),'Source removal requires explicit checkpoint handling'
delta={k:v for k,v in current.items() if baseline.get(k)!=v}
files=merge(gate['output_sha256'],delta)
for name in ['PLAN.md','STATUS.md','DECISIONS.md','docs/v1.3/M4E2_METHODS.md','docs/v1.3/M4E2_SOURCE_PREPARATION.md',
    'docs/v1.3/M4E3_DIAGNOSTICS_PREPARATION.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md',
    'docs/v1.3/M4_INCREMENT_PLAN.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md','docs/architecture-compliance-matrix.md']:
    files[name]=digest(ROOT/name)
for p in [*HERE.glob('*.py'),*HERE.glob('*.json')]:files[p.relative_to(ROOT).as_posix()]=digest(p)
# Explicitly scoped observational records: these are not full-suite acceptance.
for name in ['source-details-progress-0001','source-details-execution-context-0001']:
    folder=M4/name
    for p in folder.iterdir():
        assert p.is_file(),'Unexpected nested observational content'
        files[p.relative_to(ROOT).as_posix()]=digest(p)
blocked={'.private','build','.gradle','.cxx','.kotlin','__pycache__','temp','stage','runner-temp','host-temp'}
for name,expected in files.items():
    p=ROOT/name;assert p.resolve().is_relative_to(ROOT) and not blocked.intersection(Path(name).parts),name
    assert p.suffix.lower() not in {'.apk','.pyc','.class','.seed','.seed32','.pem','.key','.keystore','.jks','.gguf','.onnx','.safetensors'},name
    assert digest(p)==expected,name
target=HERE/'checkpoint-files.json';assert not target.exists()
target.write_text(json.dumps(dict(purpose='EXACT_E2_CHECKPOINT_TESTED_DELTA_PUBLIC_EVIDENCE_AND_DOCUMENTATION',
    prior_gate_sha256=digest(M4/'ui-query-gate-0002/gate.json'),tested_source_delta=delta,
    observational_records_are_not_acceptance=True,files=dict(sorted(files.items()))),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='PASS_CHECKPOINT_WHITELIST_NOT_COMMIT',source_delta_files=len(delta),whitelist_files=len(files))))
