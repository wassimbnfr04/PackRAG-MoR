"""Compare completed new device methods; expressly not full instrumentation acceptance."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;M4=ROOT/'artifacts/v1.3/m4'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
assert not (HERE/'partial-parity.json').exists()
observed={}
for name in ('m4-source-text.json','m4-representations.json','m4-representation-runtime.json'):
    result=subprocess.run([str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell','run-as','org.packrag.product','cat','files/'+name],capture_output=True,check=True,timeout=30)
    (HERE/name).write_bytes(result.stdout);observed[name]=hashlib.sha256(result.stdout).hexdigest();assert read(HERE/name)['status']=='PASS'
presence=read(HERE/'m4-source-text.json');assert (presence['fixed_presence_cases'],presence['whitespace_points'],presence['valid_scalars_checked'],presence['blank_resolver_checks'])==(38,29,1112064,116)
desktop=read(M4/'source-text-smoke-0001/source-text-smoke-results.json');assert desktop['status']=='PASS'
assert {r['id']:r['accepted'] for r in presence['imports']}=={r['id']:r['accepted'] for r in desktop['imports']}
expected={r['id']:r for r in desktop['tokenizer_cases']};assert len(expected)==len(presence['tokenizer_cases'])==2
for row in presence['tokenizer_cases']:
    assert row['max_embedding_abs_error']<=1e-4
    for key in ('admission','actual_tokenizer','representations','canonical_text','canonical_text_sha256'):assert row[key]==expected[row['id']][key]
representations=read(HERE/'m4-representations.json');rep_tokens=read(M4/'representation-smoke-0003/tokenizer-cases.json');assert rep_tokens['status']=='PASS'
expected={r['id']:r for r in rep_tokens['cases']};assert len(expected)==len(representations['retrieval_cases'])==14
for row in representations['retrieval_cases']:
    assert row['max_embedding_abs_error']<=1e-4 and row['max_dense_cosine_error']<=1e-4
    assert row['admission']==expected[row['id']]['admission'] and row['actual_tokenizer']==expected[row['id']]['actual_tokenizer']
    if row['admission']=='READY':assert row['representations']==expected[row['id']]['representations']
actual=read(HERE/'m4-representation-runtime.json');expected={r['id']:r for r in read(M4/'representation-smoke-0003/representation-smoke-results.json')['cases']};assert len(actual['cases'])==len(expected)==8
for row in actual['cases']:
    final=expected[row['id']]['result'];assert row['state']==final['state'] and row['actual_weight_inference']==expected[row['id']]['actual_weight_inference']
    if row['actual_weight_inference']:
        assert row['selected']==[r['chunk_id'] for r in final['selected']]
        assert row['prefill_tokens']==final['token_budget']['prefill'] and row['evidence_tokens']==final['token_budget']['evidence']
        assert row['sources']==[{k:s[k] for k in ('id','canonical_text','canonical_language','canonical_text_sha256','generator_representation')} for s in final['sources']]
    else:assert row['answer'] is None and not row['sources'] and not row['selected'] and row['prefill_tokens']==row['emitted_tokens_including_terminal']==0
(HERE/'partial-parity.json').write_text(json.dumps(dict(status='PASS_COMPLETED_METHOD_PARITY_NOT_FULL_INSTRUMENTATION_OR_MILESTONE_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),intended_build='build-0020',original_adb_bytes_sha256=observed,presence_cases=38,valid_scalars=1112064,blank_resolver_checks=116,signed_presence_imports=6,representation_actual_tokenizer_cases=14,presence_actual_tokenizer_cases=2,representation_runtime_cases=8,purpose='Early completed methods; full runner manifest/APK matching, retained regression, policy, restoration and closure still required'),indent=2)+'\n')
print('PASS completed-method presence/16 exact tokens/8 runtime provenance; full gates remain pending')
