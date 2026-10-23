"""After closure only: exact public evidence and tested D2-to-D3 source delta."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def merge(left,right):
    assert all(left[k]==right[k] for k in left.keys() & right.keys())
    return {**left,**right}
gate=read(HERE/'gate.json');assert gate['status']=='M4D3_SELECTION_FREEZING_VERIFIED_NOT_COMPLETE_M4_OR_PRODUCT'
prior=read(M4/'representation-gate-0002/gate.json')
baseline=merge(prior['source_sha256'],prior['android_source_sha256']['build-0020'])
current=merge(gate['source_sha256'],gate['android_source_sha256'])
delta={k:v for k,v in current.items() if baseline.get(k)!=v}
files=merge(gate['output_sha256'],gate['documents_at_closure']);files=merge(files,delta)
# Read-only next-milestone preparation is an operational document, not accepted E code.
preparation=ROOT/'docs/v1.3/M4E_UI_PREPARATION.md';files[preparation.relative_to(ROOT).as_posix()]=digest(preparation)
for p in [*HERE.glob('*.py'),*HERE.glob('*.json')]:files[p.relative_to(ROOT).as_posix()]=digest(p)
blocked={'.private','build','.gradle','.cxx','.kotlin','__pycache__','temp','stage','runner-temp','host-temp'}
for name,expected in files.items():
    p=ROOT/name;assert p.resolve().is_relative_to(ROOT) and not blocked.intersection(Path(name).parts),name
    assert p.suffix.lower() not in {'.apk','.pyc','.class','.seed','.seed32','.pem','.key','.keystore','.jks','.gguf','.onnx','.safetensors'},name
    assert digest(p)==expected,name
target=HERE/'checkpoint-files.json';assert not target.exists()
target.write_text(json.dumps(dict(purpose='EXACT_D3_CHECKPOINT_TESTED_DELTA_AND_PUBLIC_EVIDENCE_NOT_APK_WEIGHT_PRIVATE_CACHE',
    prior_gate_sha256=digest(M4/'representation-gate-0002/gate.json'),tested_source_delta=delta,files=dict(sorted(files.items()))),indent=2)+'\n')
print(json.dumps(dict(status='PASS_CHECKPOINT_WHITELIST_NOT_COMMIT',source_delta_files=len(delta),whitelist_files=len(files))))
