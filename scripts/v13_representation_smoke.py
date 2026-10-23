"""Real pinned English rendering integration; synthetic review labels only."""
import argparse,json,traceback
from contextlib import ExitStack
from dataclasses import asdict
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from product.packrag.config import RuntimeContractError,file_sha
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack,SessionRegistry
from product.packrag.prompt import prepare
from product.packrag.retrieval import Query,retrieve
from product.packrag.runtime import PackRAG
from scripts.v13_result_manifest import public_source_files
from scripts.v13_smoke import ROOT,owned_server,save
from scripts.v13_conflict_smoke import CountingBackend

CORPUS=ROOT/'artifacts/v1.3/m4/representation-fixtures-0001'
RUNTIME_CASES=('fr-official','ar-reviewed','missing','machine-fr','ambiguous','derived-control','canonical-control','title-control')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT);run.mkdir(parents=True,exist_ok=False)
    save(run/'inputs.json',dict(started_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256={p.relative_to(ROOT).as_posix():file_sha(p) for p in public_source_files(ROOT)},corpus_sha256=file_sha(CORPUS/'cases.json')))
    results=[];tokens=[];status='FAIL'
    try:
        reference=json.loads((CORPUS/'cases.json').read_text());public=(CORPUS/'public-key.raw').read_bytes()
        assert file_sha(CORPUS/'public-key.raw')==reference['public_key_sha256']
        encoder=GraniteEncoder(ROOT/'models/v1.3/granite')
        with ExitStack() as stack,owned_server(run) as backend:
            packs={}
            for row in reference['packs']:
                path=CORPUS/row['filename'];assert file_sha(path)==row['sha256']
                if row['import_accept']:packs[row['id']]=stack.enter_context(VerifiedPack(path,[public],developer_mode=True))
            generator=CountingBackend(backend)
            for case in reference['cases']:
                pack=packs[case['id']];query=Query(case['raw'],case['as_of'])
                candidates,ambiguous=retrieve((pack,),query,np.asarray(case['query_vector'],dtype=np.float32))
                assert not ambiguous and len(candidates)==1 and candidates[0].exact and candidates[0].relevant
                record=dict(id=case['id'],status='OBSERVED_NOT_ACCEPTANCE',admission=None,actual_tokenizer={})
                try:
                    prompt=prepare(query,(pack.identity,),candidates,generator)
                    record.update(admission='READY',actual_tokenizer=dict(tokens=list(prompt.tokens),prefill_tokens=prompt.prefill_tokens,
                        evidence_tokens=prompt.evidence_tokens,max_new=prompt.max_new_tokens,selected=[c.chunk['chunk_id'] for c in prompt.evidence]),
                        representations=[asdict(r) for r in prompt.representations])
                except RuntimeContractError as error:record['admission']=str(error)
                save(run/(case['id']+'-tokenizer-observed.json'),record)
                assert record['admission']==('READY' if case['expected_state']=='ANSWER_ACCEPTED' else case['expected_state']),case['id']
                if record['admission']=='READY':
                    assert record['representations']==[case['generator_representation']]
                    assert prompt.prefill_tokens<=1536 and prompt.evidence_tokens<=1200 and len(prompt.evidence)<=4 and prompt.max_new_tokens<=512
                record['status']='PASS';tokens.append(record)
            save(run/'tokenizer-cases.json',dict(status='PASS',cases=tokens,purpose='ACTUAL_FULL_TEMPLATE_TOKENS_STORED_ACTUAL_QUERY_VECTOR_NOT_WEIGHT_INFERENCE'))
            for label in RUNTIME_CASES:
                case=next(c for c in reference['cases'] if c['id']==label);registry=SessionRegistry();registry.activate(packs[label])
                before=generator.calls;result=PackRAG(registry,encoder,generator).answer(Query(case['raw'],case['as_of']))
                save(run/(label+'-observed.json'),dict(id=label,status='OBSERVED_NOT_ACCEPTANCE',result=result,
                    generate_calls_for_case=generator.calls-before,diagnostic_final_candidate_not_product_answer=generator.last_final_candidate if generator.calls>before else None))
                assert result['state']==case['expected_state'],label
                if result['state']!='ANSWER_ACCEPTED':assert generator.calls==before and not result['selected'] and not result['sources'] and result['answer'] is None
                else:
                    assert generator.calls==before+1 and '74 °C' in result['answer'] and result['sources'] and '</think>' not in result['answer']
                    source=result['sources'][0]
                    assert (source['canonical_text'],source['canonical_language'],source['canonical_text_sha256'])==(case['canonical_text'],case['canonical_language'],case['canonical_text_sha256'])
                    assert source['generator_representation']==case['generator_representation']==result['selected'][0]['generator_representation']
                item=dict(id=label,status='PASS',result=result,generate_calls_for_case=generator.calls-before,
                    actual_weight_inference=case['expected_state']=='ANSWER_ACCEPTED',model_load_not_excluded=True)
                results.append(item);save(run/(label+'.json'),item);print(label,result['state'],'PASS',flush=True)
        status='PASS'
    except Exception:
        (run/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        save(run/'representation-smoke-results.json',dict(status=status,cases=results,tokenizer_cases=len(tokens),
            purpose='REAL_LFM_SYNTHETIC_TRANSLATION_PROTOCOL_NOT_REAL_REVIEW_RELEASE_GOLD_CALIBRATION_OR_PERFORMANCE',raw_reasoning_persisted=False))
        save(run/'output-hashes.json',{p.relative_to(run).as_posix():file_sha(p) for p in run.rglob('*') if p.is_file() and p.name!='output-hashes.json'})

if __name__=='__main__':main()
