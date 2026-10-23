"""Exact D3 cross-platform contracts; explicitly after-observation controls."""
import argparse,hashlib,json,traceback,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def conflict(value):return {key:item for key,item in value.items() if key!='resolved'}
def compare_origins(android,desktop):
    assert len(android)==len(desktop)
    py={o['chunk']['chunk_id']:o for o in desktop}
    aliases={'original_sha256':'sha256_original','effective_until':'effective_until_excl'}
    for origin in android:
        expected=py[origin['chunk']['chunk_id']]
        assert origin['identity']==expected['identity']
        for key,value in origin['chunk'].items():assert value==expected['chunk'][aliases.get(key,key)],('origin_chunk',key)
        assert origin['metadata']==expected['source_metadata']
        assert origin['derived']==expected['derived_texts']
        for key in ('exact','sparse_rank','dense_rank'):assert origin[key]==expected[key]
        assert abs(origin['cosine']-expected['cosine'])<=1e-4 and abs(origin['rrf']-expected['rrf'])<=1e-12
        assert [conflict(v) for v in origin['conflicts']]==expected['conflicts']
        assert origin['calibration']==dict(status=expected['calibration']['status'],agreed=expected['calibration']['min_agreed_dense_cosine'],dense_only=expected['calibration']['min_dense_only_cosine'])

def verify(run):
    manifest=read(run/'instrumentation-manifest.json');assert manifest['status']=='PASS'
    collected=read(run/'collected-results.json');assert collected['status']=='PASS'
    assert collected['apk_sha256']==manifest['apk_sha256']
    for name,value in collected['saved_sha256'].items():
        assert digest(run/'original-adb'/name)==value
        assert read(run/name)==read(run/'original-adb'/name)
    expected={v['id']:v for v in read(M4/'selection-smoke-0002/tokenizer-cases.json')['cases']}
    original=read(M4/'selection-fixtures-0002/cases.json');format=read(M4/'selection-format-reference-0001/case.json')
    reference={v['id']:v for v in original['cases']};reference[format['id']]=format
    tokenizer=read(run/'m4-selection-tokenizer.json');assert tokenizer['status']=='PASS'
    assert tokenizer['fixed_plans']==28 and tokenizer['signed_tokenizer_cases']==8 and tokenizer['post_observation_format_controls']==1
    assert len(tokenizer['cases'])==9
    for row in tokenizer['cases']:
        label=row['id'];assert row['status']=='PASS' and row['max_embedding_abs_error']<=1e-4
        case=reference[label];assert row['admission']==case['expected_admission']
        assert [v['chunk_id'] for v in row['candidates']]==case['expected_pool']
        assert [v['fused_rank'] for v in row['candidates']]==list(range(1,len(case['expected_pool'])+1))
        if row['admission']=='READY':
            assert row['actual_tokenizer']=={k:case['actual_tokenizer'][k] for k in ('tokens','prefill_tokens','evidence_tokens','max_new','selected')},(label,'actual_tokenizer')
            assert [v['rendering'] for v in row['evidence']]==case['actual_tokenizer']['representations']
            assert row['selection']==(format['selection'] if label=='atomic-format-control' else expected[label]['selection'])
        else:assert row['selection']==expected[label]['selection']
    dedup=tokenizer['deduplicated_origin_control'];assert dedup['status']=='PASS'
    assert len(dedup['origin_records'])==2
    assert {v['chunk']['locator'] for v in dedup['origin_records']}=={'first','second'}
    assert len({v['chunk']['chunk_id'] for v in dedup['origin_records']})==2
    runtimes=read(run/'m4-selection-runtime.json');assert runtimes['status']=='PASS' and len(runtimes['cases'])==8
    for row in runtimes['cases']:
        label=row['id'];desktop=read(M4/'selection-smoke-0002'/(label+'.json'));py=desktop['result']
        assert row['status']=='PASS' and row['state']==py['state'] and row['generate_calls']==desktop['generate_calls_for_case']
        assert row['selection']==py['selection']
        assert row['selected']==[v['chunk_id'] for v in py['selected']]
        budget=py.get('token_budget')
        assert row['prefill_tokens']==(budget['prefill'] if budget else 0)
        assert row['evidence_tokens']==(budget['evidence'] if budget else 0)
        for evidence,selected in zip(row['evidence'],py['selected']):
            assert evidence['identity']==[selected['pack_id'],selected['version'],selected['manifest_sha256']]
            assert evidence['chunk']['chunk_id']==selected['chunk_id'] and evidence['fused_rank']==selected['fused_rank']
            assert evidence['rendering']==selected['generator_representation'] and evidence['source_metadata']==selected['source_metadata']
            assert [conflict(v) for v in evidence['conflicts']]==selected['conflicts']
            compare_origins(evidence['origin_records'],selected['origin_records'])
        assert [s['id'] for s in row['sources']]==[s['id'] for s in py['sources']]
        for source,expected_source in zip(row['sources'],py['sources']):
            for key in ('canonical_text','canonical_text_sha256','chunk_id','source_id','fused_rank','original_sha256'):assert source[key]==expected_source[key]
            assert source['identity']==[expected_source['pack_id'],expected_source['version'],expected_source['manifest_sha256']]
            compare_origins(source['origin_records'],expected_source['origins'])
        if row['state']=='ANSWER_ACCEPTED':assert row['answer'] and '74 °C' in row['answer'] and '</think>' not in row['answer']
        else:assert row['answer'] is None and not row['sources']
    guards=read(run/'m4-selection-guards.json');assert guards['status']=='PASS' and len(guards['cases'])==2
    assert {(v['id'],v['state'],v['generate_calls']) for v in guards['cases']}=={('manifest','ACTIVE_PACK_CHANGED',0),('backend','GENERATOR_IDENTITY_CHANGED',0)}
    return dict(actual_tokenizer_admission_cases=9,runtime_state_cases=8,pure_fixed_plans=28,guards=2,deduplicated_local_origins=2,
        format_control='POST_OBSERVATION_NOT_HELDOUT',original_question='CONSERVATIVE_OUTPUT_REJECTION_ORIGINAL_SUPPORTED_ACCEPTANCE_REMAINS_FAIL',
        natural_language_wording_byte_equality_required=False,original_byte_captures=len(collected['saved_sha256']))

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--target',type=Path,required=True);a=p.parse_args()
    run=a.run.resolve();target=a.target.resolve();assert run.is_relative_to(M4) and target.is_relative_to(M4) and not target.exists()
    try:record=verify(run)
    except Exception:
        failure=target.with_suffix('.failure.txt');assert not failure.exists();failure.write_text(traceback.format_exc());raise
    target.write_text(json.dumps(dict(status='PASS_D3_SELECTION_PARITY_NOT_COMPLETE_MILESTONE',recorded_utc=datetime.now(timezone.utc).isoformat(),
        verifier_sha256=digest(Path(__file__)),run=str(run.relative_to(ROOT)),**record),indent=2)+'\n');print('D3_SELECTION_PARITY_PASS_NOT_FULL_CLOSURE')

if __name__=='__main__':main()
