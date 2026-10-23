"""Repair one overbroad unexecuted acceptance-helper substitution, preserving it."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;M4=ROOT/'artifacts/v1.3/m4'
recovery=HERE/'preparation-repair';assert not recovery.exists();recovery.mkdir()
before={}
for name in ('prepare_closure.py','verify_and_record.py','closure-derivation.json'):
    payload=(HERE/name).read_bytes();(recovery/name).write_bytes(payload);before[name]=hashlib.sha256(payload).hexdigest()
path=HERE/'prepare_closure.py';source=path.read_text();old="('== 28','== 29')";new="('[\"test_methods\"] == 28','[\"test_methods\"] == 29')";assert old in source;path.write_text(source.replace(old,new),encoding='utf-8')
path=HERE/'verify_and_record.py';source=path.read_text();old='len(result["query_contract_cases"]) == 29';new='len(result["query_contract_cases"]) == 28';assert old in source;path.write_text(source.replace(old,new),encoding='utf-8')
source=(M4/'representation-gate-0001/prephone_audit.py').read_text()
for old,new in [('run-0009','run-0010'),('tests=792','tests=954'),('smoke-0009','smoke-0010'),('conflict-smoke-0005','conflict-smoke-0006'),('relevance-smoke-0002','relevance-smoke-0003'),('representation-smoke-0002','representation-smoke-0003'),('build-0018','build-0020'),('build-0019','build-0021'),("['test_methods']==28","['test_methods']==29")]:assert old in source;source=source.replace(old,new)
source=source.replace("gates={}\n", "presence=read(M4/'source-text-smoke-0001/source-text-smoke-results.json');assert presence['status']=='PASS' and len(presence['tokenizer_cases'])==2\nassert read(M4/'source-text-smoke-0001/inputs.json')['source_sha256']==runtime\ngates={}\n")
(HERE/'prephone_audit.py').write_text(source,encoding='utf-8')
for path in HERE.glob('*.py'):compile(path.read_text(),str(path),'exec')
(HERE/'preparation-repair.json').write_text(json.dumps(dict(status='UNEXECUTED_HELPER_REPAIRED_NOT_PRODUCT_FAILURE_OR_ACCEPTANCE',before_sha256=before,after_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('prepare_closure.py','verify_and_record.py','prephone_audit.py')},reason='Code review found host-count replacement also changed unchanged query-contract28 to29; scope replacement to host summary. No acceptance helper was executed before repair.'),indent=2)+'\n')
print('Repaired and preserved unexecuted closure helper; syntax passes')
