"""Save completed representation method; never claim whole running gate acceptance."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;M4=ROOT/'artifacts/v1.3/m4'
path=HERE/'m4-representations.json';assert not path.exists()
command=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell','run-as','org.packrag.product','cat','files/m4-representations.json']
result=subprocess.run(command,capture_output=True,check=True,timeout=30);path.write_bytes(result.stdout)
phone=json.loads(result.stdout);assert phone['status']=='PASS' and phone['fixed_contract_cases']==32 and phone['signed_packs']==20
assert len(phone['invalid_imports'])==6 and all(not r['accepted'] for r in phone['invalid_imports'])
desktop=json.loads((M4/'representation-smoke-0002/tokenizer-cases.json').read_text());assert desktop['status']=='PASS'
expected={r['id']:r for r in desktop['cases']};assert len(expected)==len(phone['retrieval_cases'])==14
for row in phone['retrieval_cases']:
    oracle=expected[row['id']];assert row['status']=='PASS' and row['max_embedding_abs_error']<=1e-4 and row['max_dense_cosine_error']<=1e-4
    assert row['admission']==oracle['admission'] and row['actual_tokenizer']==oracle['actual_tokenizer']
    if row['admission']=='READY':assert row['representations']==oracle['representations']
build=M4/'build-0018';apks={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in build.glob('*.apk')}
record=dict(status='PASS_COMPLETED_METHOD_PARITY_NOT_FULL_INSTRUMENTATION_OR_MILESTONE_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    serial='R3CT908DHHR',apk_sha256=apks,original_adb_bytes_sha256=hashlib.sha256(result.stdout).hexdigest(),fixed_cases=32,signed_packs=20,rejected_imports=6,
    exact_tokenizer_admission_cases=14,maximum_embedding_error=max(r['max_embedding_abs_error'] for r in phone['retrieval_cases']),
    maximum_cosine_error=max(r['max_dense_cosine_error'] for r in phone['retrieval_cases']),
    remaining='Eight actual runtime and retained development methods; compiled policy, restoration and closure remain required',
    command=command)
(HERE/'partial-parity.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
