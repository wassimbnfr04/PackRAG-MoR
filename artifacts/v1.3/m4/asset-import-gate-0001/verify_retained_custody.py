"""Explicit immutable public lists only; independent new F2 custody observation."""
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
target=HERE/args.output;assert target.parent==HERE and not target.exists() and target.suffix=='.json'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def check(mapping):
    for name,value in mapping.items():
        path=Path(name);assert not path.is_absolute() and '..' not in path.parts and '.private' not in path.parts
        assert not {'temp','stage','runner-temp','host-temp','pytest-temp'}.intersection(path.parts)
        assert path.suffix.lower() not in {'.seed','.seed32','.key','.jks','.pem','.keystore'}
        p=ROOT/path;assert p.resolve().is_relative_to(ROOT) and not p.is_symlink() and sha(p)==value,name
f1=read(M4/'asset-readiness-gate-0001/gate.json');history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files']
assert len(f1['output_sha256'])==406 and len(f1['source_sha256'])==188 and len(history)==587
check(f1['output_sha256']);check(f1['source_sha256']);check(history)
record=dict(status='PASS_ACCEPTED_F1_406_HISTORICAL587_AND_PYTHON188_PUBLIC_IDENTITIES_UNCHANGED',recorded_utc=datetime.now(timezone.utc).isoformat(),
    f1_outputs=406,historical_files=587,python_runtime_inputs=188,f1_gate_sha256=sha(M4/'asset-readiness-gate-0001/gate.json'),
    scope='Read only exact accepted public mappings, no private-key custody or temporary traversal. Unchanged earlier test evidence is not a newly executed regression suite; fresh comprehensive validation is still required at F4. F2 Android inputs intentionally differ and bind to each new build.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'],flush=True)
