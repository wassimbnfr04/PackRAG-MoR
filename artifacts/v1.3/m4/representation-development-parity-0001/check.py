"""Complete saved development parity; policy/restoration are explicitly pending."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;M4=ROOT/'artifacts/v1.3/m4'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'parity.json';assert not target.exists()
run=M4/'device-representations-0001';manifest=read(run/'instrumentation-manifest.json');assert manifest['status']=='PASS'
collection=read(run/'collected-results.json');assert collection['status']=='PASS' and len(collection['saved_sha256'])==26
for name,value in collection['saved_sha256'].items():
    assert digest(run/'original-adb'/name)==value and read(run/name)==read(run/'original-adb'/name)
    assert read(run/name)['status']=='PASS'
results=[]
for prefix,device_file,desktop_run,desktop_result,token_count,runtime_count in [
    ('representation','m4-representations.json','representation-smoke-0002','representation-smoke-results.json',14,8),
    ('relevance','m4-relevance.json','relevance-smoke-0002','relevance-smoke-results.json',8,4),
    ('conflict','m4-conflicts.json','conflict-smoke-0005','conflict-smoke-results.json',19,7)]:
    device=read(run/device_file);oracle={r['id']:r for r in read(M4/desktop_run/'tokenizer-cases.json')['cases']}
    assert len(oracle)==len(device['retrieval_cases'])==token_count
    for row in device['retrieval_cases']:
        expected=oracle[row['id']];assert row['status']=='PASS' and row['max_embedding_abs_error']<=1e-4 and row['max_dense_cosine_error']<=1e-4
        assert row['admission']==expected['admission'] and row['actual_tokenizer']==expected['actual_tokenizer']
        if prefix=='representation' and row['admission']=='READY':assert row['representations']==expected['representations']
    runtime_file='m4-representation-runtime.json' if prefix=='representation' else 'm4-'+prefix+'-runtime.json'
    actual=read(run/runtime_file);expected={r['id']:r for r in read(M4/desktop_run/desktop_result)['cases']}
    assert len(actual['cases'])==len(expected)==runtime_count
    for row in actual['cases']:
        desktop=expected[row['id']];final=desktop['result']
        assert row['status']==desktop['status']=='PASS' and row['state']==final['state'] and row['actual_weight_inference']==desktop['actual_weight_inference']
        if row['actual_weight_inference']:
            assert '74' in row['answer'] and row['prefill_tokens']==final['token_budget']['prefill'] and row['evidence_tokens']==final['token_budget']['evidence']
            assert row['selected']==[s['chunk_id'] for s in final['selected']]
            if prefix=='representation':assert row['sources']==[{k:s[k] for k in ('id','canonical_text','canonical_language','canonical_text_sha256','generator_representation')} for s in final['sources']]
        else:assert row['answer'] is None and not row['selected'] and row['prefill_tokens']==row['emitted_tokens_including_terminal']==0
    results.append(dict(family=prefix,status='PASS',exact_tokenizer_admission_cases=token_count,actual_runtime_cases=runtime_count))
cancel=read(run/'m2-generator-cancellation.json');assert cancel['status']=='PASS' and cancel['native_cancel_stop']==2 and cancel['post_cancel_recovery_state']=='ANSWER_ACCEPTED'
record=dict(status='PASS_COMPLETE_DEVELOPMENT_AND_PARITY_NOT_POLICY_RESTORATION_OR_MILESTONE_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    development_methods=26,whole_instrumentation_seconds=1586.006,saved_results=26,families=results,exact_tokenizer_cases=41,runtime_state_cases=19,
    native_cancel_return_ms=cancel['cancel_return_ms'],apk_sha256=manifest['apk_sha256'],collected_sha256=digest(run/'collected-results.json'),
    remaining='Compiled-policy21 methods/results, development restoration0009 and complete immutable closure/checkpoint; D3 still blocked on D2 acceptance')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record))
