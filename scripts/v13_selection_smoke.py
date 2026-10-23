"""Actual pinned selection/tokenizer/runtime gate; synthetic protocol content only."""
import argparse
from contextlib import ExitStack
from dataclasses import asdict
from datetime import datetime,timezone
import json
from pathlib import Path
import traceback
import numpy as np

from product.packrag.config import file_sha,RuntimeContractError
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack,SessionRegistry
from product.packrag.prompt import prepare
from product.packrag.retrieval import Query,retrieve
from product.packrag.runtime import PackRAG
from scripts.v13_result_manifest import public_source_files
from scripts.v13_smoke import ROOT,owned_server,save
from scripts.v13_conflict_smoke import CountingBackend

CORPUS=ROOT/'artifacts/v1.3/m4/selection-fixtures-0002'
RUNTIME_CASES=('atomic-last','five-mandatory','missing-global','mandatory-oversize','optional-oversize','all-oversize','boundary1201')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT/'artifacts/v1.3/m4');run.mkdir(parents=True,exist_ok=False)
    sources={p.relative_to(ROOT).as_posix():file_sha(p) for p in public_source_files(ROOT)}
    save(run/'inputs.json',dict(started_at=datetime.now(timezone.utc).isoformat(),source_sha256=sources,
        corpus_sha256=file_sha(CORPUS/'cases.json'),purpose='SYNTHETIC_TEST_ONLY_NOT_FINAL_OWNER_PACKS'))
    status='FAIL';tokens=[];results=[]
    try:
        reference=json.loads((CORPUS/'cases.json').read_text());public=(CORPUS/'public-key.raw').read_bytes()
        assert file_sha(CORPUS/'public-key.raw')==reference['public_key_sha256']
        encoder=GraniteEncoder(ROOT/'models/v1.3/granite')
        with ExitStack() as stack,owned_server(run) as backend:
            packs={}
            for row in reference['packs']:
                path=CORPUS/row['filename'];assert file_sha(path)==row['sha256']
                packs[row['id']]=stack.enter_context(VerifiedPack(path,[public],developer_mode=True))
            generator=CountingBackend(backend)
            for case in reference['cases']:
                pack=packs[case['id']];query=Query(case['raw'],case['as_of'],case['jurisdiction'])
                vector=encoder.encode(query.normalized);error=float(np.max(np.abs(vector-np.asarray(case['query_vector'],dtype=np.float32))))
                assert error<=1e-4
                candidates,ambiguous=retrieve((pack,),query,vector)
                assert not ambiguous and [item.chunk['chunk_id'] for item in candidates]==case['expected_pool']
                row=dict(id=case['id'],status='OBSERVED_NOT_ACCEPTANCE',admission=None,actual_tokenizer={},max_embedding_abs_error=error)
                try:
                    prompt=prepare(query,(pack.identity,),candidates,generator)
                    row.update(admission='READY',actual_tokenizer=dict(tokens=list(prompt.tokens),prefill_tokens=prompt.prefill_tokens,
                        evidence_tokens=prompt.evidence_tokens,max_new=prompt.max_new_tokens,selected=[item.chunk['chunk_id'] for item in prompt.evidence]),
                        selection=asdict(prompt.selection),representations=[asdict(v) for v in prompt.representations])
                    reverse=prepare(query,(pack.identity,),list(reversed(candidates)),generator)
                    assert reverse.tokens==prompt.tokens and reverse.selection==prompt.selection
                except RuntimeContractError as failure:
                    row['admission']=str(failure)
                    if hasattr(failure,'selection'):row['selection']=asdict(failure.selection)
                save(run/(case['id']+'-tokenizer-observed.json'),row)
                assert row['admission']==case['expected_admission'],case['id']
                if row['admission']=='READY':
                    old=case['actual_tokenizer'];actual=row['actual_tokenizer']
                    assert all(actual[key]==old[key] for key in ('tokens','prefill_tokens','evidence_tokens','max_new','selected'))
                    assert row['representations']==old['representations']
                else:
                    assert row['selection']['admission']==row['admission'] and not row['selection']['keys']
                    assert len(row['selection']['decisions'])==len(candidates)
                row['status']='PASS';tokens.append(row)
            save(run/'tokenizer-cases.json',dict(status='PASS',cases=tokens,scope='ACTUAL_GRANITE_GGUF_TEMPLATE_AND_SELECTION_NOT_WEIGHT_INFERENCE'))
            format_case=json.loads((ROOT/'artifacts/v1.3/m4/selection-format-reference-0001/case.json').read_text())
            assert format_case['original_corpus_sha256']==file_sha(CORPUS/'cases.json')
            for identity in RUNTIME_CASES+('atomic-format-control',):
                case=format_case if identity=='atomic-format-control' else next(v for v in reference['cases'] if v['id']==identity)
                pack=packs['atomic-last' if identity=='atomic-format-control' else identity];registry=SessionRegistry();registry.activate(pack)
                before=generator.calls;query=Query(case['raw'],case['as_of'],case['jurisdiction'])
                result=PackRAG(registry,encoder,generator).answer(query)
                expected='OUTPUT_REJECTED' if identity=='atomic-last' else 'ANSWER_ACCEPTED' if case['expected_admission']=='READY' else case['expected_admission']
                row=dict(id=identity,status='OBSERVED_NOT_ACCEPTANCE',expected_state=expected,result=result,
                    generate_calls_for_case=generator.calls-before,diagnostic_final_candidate_not_product_answer=generator.last_final_candidate if generator.calls>before else None)
                save(run/(identity+'-runtime-observed.json'),row)
                assert result['state']==expected,identity
                if expected=='ANSWER_ACCEPTED':
                    assert generator.calls==before+1 and result['sources'] and '</think>' not in result['answer']
                    assert [item['chunk_id'] for item in result['selected']]==case['expected_selected']
                    assert result['selected'][0]['fused_rank']==1 and result['selected'][-1]['fused_rank']==5
                    by_id={row['id']:row for row in result['selected']}
                    for source in result['sources']:
                        assert source['manifest_sha256']==pack.identity[2]
                        assert source['chunk_id']==by_id[source['id']]['chunk_id']
                        assert source['original_sha256']==by_id[source['id']]['original_sha256']
                elif identity=='atomic-last':
                    assert generator.calls==before+1 and result['answer'] is None and not result['sources']
                    assert result['rejection_reason']=='uncited_paragraph'
                    assert [item['chunk_id'] for item in result['selected']]==case['expected_selected']
                    row['scope']='POST_OBSERVATION_CONSERVATIVE_OUTPUT_REGRESSION_ORIGINAL_SUPPORTED_ACCEPTANCE_FAILED_IN_SMOKE0001'
                else:
                    assert generator.calls==before and result['answer'] is None and not result['selected'] and not result['sources']
                    assert result['selection']['admission']==expected
                row['status']='PASS';results.append(row);save(run/(identity+'.json'),row)
                print(identity,result['state'],'PASS',flush=True)
        assert all(file_sha(ROOT/name)==value for name,value in sources.items()),'Source changed during selection smoke'
        status='PASS'
    except Exception:
        (run/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        save(run/'selection-smoke-results.json',dict(status=status,cases=results,tokenizer_cases=len(tokens),raw_reasoning_persisted=False,
            scope='REAL_LFM_SYNTHETIC_SELECTION_PROTOCOL_NOT_FINAL_CONTENT_RELEASE_CALIBRATION_PACKBENCH_OR_PERFORMANCE'))
        save(run/'output-hashes.json',{p.relative_to(run).as_posix():file_sha(p) for p in run.rglob('*') if p.is_file() and p.name!='output-hashes.json'})


if __name__=='__main__':main()
