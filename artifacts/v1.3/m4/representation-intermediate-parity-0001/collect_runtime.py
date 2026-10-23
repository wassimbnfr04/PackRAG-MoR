"""Completed new runtime method parity while the complete gate still runs."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;M4=ROOT/'artifacts/v1.3/m4'
path=HERE/'m4-representation-runtime.json';assert not path.exists()
command=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell','run-as','org.packrag.product','cat','files/m4-representation-runtime.json']
result=subprocess.run(command,capture_output=True,check=True,timeout=30);path.write_bytes(result.stdout)
phone=json.loads(result.stdout);assert phone['status']=='PASS' and len(phone['cases'])==8
desktop=json.loads((M4/'representation-smoke-0002/representation-smoke-results.json').read_text());assert desktop['status']=='PASS'
expected={r['id']:r for r in desktop['cases']};assert set(expected)=={r['id'] for r in phone['cases']}
for row in phone['cases']:
    oracle=expected[row['id']];final=oracle['result']
    assert row['status']==oracle['status']=='PASS' and row['state']==final['state']
    assert row['actual_weight_inference']==oracle['actual_weight_inference']
    if row['actual_weight_inference']:
        assert row['state']=='ANSWER_ACCEPTED' and '74 °C' in row['answer'] and '</think>' not in row['answer']
        assert row['prefill_tokens']==final['token_budget']['prefill'] and row['evidence_tokens']==final['token_budget']['evidence']
        assert row['selected']==[r['chunk_id'] for r in final['selected']]
        assert row['sources']==[{k:s[k] for k in ('id','canonical_text','canonical_language','canonical_text_sha256','generator_representation')} for s in final['sources']]
    else:assert row['answer'] is None and not row['sources'] and not row['selected'] and row['prefill_tokens']==row['emitted_tokens_including_terminal']==0
record=dict(status='PASS_COMPLETED_RUNTIME_METHOD_PARITY_NOT_FULL_INSTRUMENTATION_OR_MILESTONE_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    original_adb_bytes_sha256=hashlib.sha256(result.stdout).hexdigest(),runtime_cases=8,accepted_french_arabic=2,zero_generation_guards=6,
    source='Exact state/selected supported token budget/canonical bytes and generator provenance; final natural language wording is not required to match desktop byte for byte',
    apk_sha256=json.loads((HERE/'partial-parity.json').read_text())['apk_sha256'],remaining='Retained full development/policy/restoration/closure',command=command)
(HERE/'runtime-parity.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
