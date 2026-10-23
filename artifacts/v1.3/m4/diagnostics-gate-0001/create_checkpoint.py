"""Only after E3 closure: exact tested delta, public evidence and durable documents."""
import hashlib,json
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def merge(a,b):
    assert all(a[n]==b[n] for n in a.keys() & b.keys());return {**a,**b}
target=HERE/'checkpoint-files.json';assert not target.exists();gate=read(HERE/'gate.json')
assert gate['status']=='M4E3_OWNED_DIAGNOSTICS_EXECUTION_LIFECYCLE_AND_UI_VERIFIED_NOT_COMPLETE_M4_OR_PRODUCT'
prior=read(M4/'source-details-gate-0001/gate.json')
baseline=merge(prior['source_sha256'],prior['android_source_sha256']);current=merge(gate['source_sha256'],gate['android_source_sha256'])
assert not baseline.keys()-current.keys()
delta={n:v for n,v in current.items() if baseline.get(n)!=v};files=merge(gate['output_sha256'],delta)
for n in ['PLAN.md','STATUS.md','DECISIONS.md','docs/v1.3/M4E3_DIAGNOSTICS_PREPARATION.md','docs/v1.3/M4E3_METHODS.md',
    'docs/v1.3/M4E3_LIFECYCLE_CONTROLS.md','docs/v1.3/M4E3_EVIDENCE_INDEX.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md',
    'docs/v1.3/M4_INCREMENT_PLAN.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md','docs/architecture-compliance-matrix.md','docs/v1.3/M4F_ASSET_READINESS_PREPARATION.md']:
    files[n]=sha(ROOT/n)
for p in [*HERE.glob('*.py'),*HERE.glob('*.json')]:files[p.relative_to(ROOT).as_posix()]=sha(p)
blocked={'.private','build','.gradle','.cxx','.kotlin','__pycache__','temp','stage','runner-temp','host-temp'}
forbidden={'.apk','.pyc','.class','.seed','.seed32','.pem','.key','.keystore','.jks','.gguf','.onnx','.safetensors'}
for n,v in files.items():
    p=ROOT/n;assert not blocked.intersection(part.lower() for part in Path(n).parts) and p.suffix.lower() not in forbidden,n
    assert p.resolve().is_relative_to(ROOT) and sha(p)==v,n
reader=M4/'source-details-gate-0001/checkpoint_git.py'
accepted=read(M4/'source-details-gate-0001/checkpoint-files.json')['files'];assert sha(reader)==accepted[reader.relative_to(ROOT).as_posix()]
spec=spec_from_file_location('e3_checkpoint_git',reader);module=module_from_spec(spec);spec.loader.exec_module(module)
assert module.git('rev-parse','HEAD').stdout.decode().strip()=='b25ebfcf9dad3b340c92bacbcc1313bd0c479ffc'
blobs=module.blobs('HEAD',sorted(accepted))
for n,v in accepted.items():assert blobs[n] is not None and hashlib.sha256(blobs[n]).hexdigest()==v,n
target.write_text(json.dumps(dict(purpose='EXACT_E3_CHECKPOINT_TESTED_DELTA_PUBLIC_EVIDENCE_AND_DURABLE_DOCUMENTS',
    prior_e2_head='b25ebfcf9dad3b340c92bacbcc1313bd0c479ffc',prior_e2_gate_sha256=sha(M4/'source-details-gate-0001/gate.json'),
    tested_source_delta=delta,files=dict(sorted(files.items())),scope='Public whitelist only. Historical failure and partial scopes preserved; no APK/model/private custody in Git. Local APKs retain separate whole-file hashes.'),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='PASS_E3_EXACT_CHECKPOINT_WHITELIST_NOT_STAGED_OR_COMMITTED',source_delta_files=len(delta),files=len(files))))
