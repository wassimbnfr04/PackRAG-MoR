"""Save completed methods' actual ADB observations while the full gate still runs."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];M4=ROOT/'artifacts/v1.3/m4';out=M4/'relevance-intermediate-parity-0001'
assert not out.exists();out.mkdir();records={}
names=['m4-relevance.json','m4-relevance-runtime.json','m4-conflicts.json','m4-conflict-runtime.json','m4-query-identifiers.json']
for name in names:
    result=subprocess.run([str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell','run-as','org.packrag.product','cat','files/'+name],check=True,capture_output=True,timeout=30)
    (out/name).write_bytes(result.stdout);records[name]=json.loads(result.stdout);assert records[name]['status']=='PASS'
for name,folder in [('m4-relevance.json','relevance-smoke-0001'),('m4-conflicts.json','conflict-smoke-0004')]:
    reference=json.loads((M4/folder/'tokenizer-cases.json').read_text());expected={r['id']:r for r in reference['cases']}
    actual=records[name]['retrieval_cases'];assert len(actual)==len(expected)
    for row in actual:
        assert row['admission']==expected[row['id']]['admission'] and row['actual_tokenizer']==expected[row['id']]['actual_tokenizer']
        assert row['max_embedding_abs_error']<=1e-4 and row['max_dense_cosine_error']<=1e-4
for name,folder,filename in [('m4-relevance-runtime.json','relevance-smoke-0001','relevance-smoke-results.json'),('m4-conflict-runtime.json','conflict-smoke-0004','conflict-smoke-results.json')]:
    expected={r['id']:r for r in json.loads((M4/folder/filename).read_text())['cases']}
    for row in records[name]['cases']:
        desktop=expected[row['id']]['result'];assert row['state']==desktop['state']
        if row['actual_weight_inference']:
            assert row['selected']==[r['chunk_id'] for r in desktop['selected']]
            assert row['prefill_tokens']==desktop['token_budget']['prefill'] and row['evidence_tokens']==desktop['token_budget']['evidence']
        else:assert row['prefill_tokens']==row['emitted_tokens_including_terminal']==0 and not row['selected']
assert next(r for r in records['m4-conflicts.json']['retrieval_cases'] if r['id']=='BEFORE_CAP')['candidate_count']==32
assert next(r for r in records['m4-query-identifiers.json']['retrieval_cases'] if r['id']=='AMBIGUITY_BEFORE_LOCAL_CAP')['candidate_count']==32
record=dict(status='PASS_COMPLETED_METHOD_PARITY_NOT_FULL_INSTRUMENTATION_OR_MILESTONE_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    current_phone_gate='device-relevance-0001 still running',new_tokenizer_scenarios=8,retained_conflict_tokenizer_scenarios=19,
    new_runtime_cases=4,retained_conflict_runtime_cases=7,both_changed_overflow_counts=32,
    observed_adb_bytes_sha256={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in names},script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(out/'partial-parity.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record))
