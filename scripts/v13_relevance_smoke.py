"""Actual pinned LFM/Granite D1 integration and actual full-template tokenizer.

The new signed synthetic calibration fields are fixed protocol controls, not
measured relevance/calibration or real source/answerability gold.
"""
import argparse
import json
import traceback
from contextlib import ExitStack
from datetime import datetime, timezone
import numpy as np
from product.packrag.config import file_sha
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack, SessionRegistry
from product.packrag.prompt import prepare
from product.packrag.retrieval import Query, retrieve
from product.packrag.runtime import PackRAG
from scripts.v13_result_manifest import public_source_files
from scripts.v13_smoke import ROOT, owned_server, save
from scripts.v13_conflict_smoke import CountingBackend
from pathlib import Path

CORPUS=ROOT/'artifacts/v1.3/m4/relevance-fixtures-0001'
RUNTIME_CASES=('TOP_FAIL_LOWER_PASS','TOP_UNCAL_LOWER_PASS','TOP_PASS_LOWER_PASS','LEGACY_STATUS_DEFAULT')

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
                packs[row['id']]=stack.enter_context(VerifiedPack(path,[public],developer_mode=True))
            generator=CountingBackend(backend)
            for case in reference['cases']:
                active=tuple(packs[n] for n in case['packs']);query=Query(case['raw'],case['as_of'])
                candidates,ambiguous=retrieve(active,query,np.asarray(case['query_vector'],dtype=np.float32))
                assert not ambiguous and [c.relevant for c in candidates]==case['expected_relevant']
                record=dict(id=case['id'],status='PASS',admission='NO_RELEVANT_EVIDENCE',actual_tokenizer={})
                if any(c.relevant for c in candidates):
                    prompt=prepare(query,tuple(p.identity for p in active),candidates,generator)
                    record.update(admission='READY',actual_tokenizer=dict(tokens=list(prompt.tokens),prefill_tokens=prompt.prefill_tokens,
                        evidence_tokens=prompt.evidence_tokens,max_new=prompt.max_new_tokens,selected=[c.chunk['chunk_id'] for c in prompt.evidence]))
                    assert prompt.prefill_tokens<=1536 and prompt.evidence_tokens<=1200 and len(prompt.evidence)<=4 and prompt.max_new_tokens<=512
                tokens.append(record)
            save(run/'tokenizer-cases.json',dict(status='PASS',cases=tokens,purpose='ACTUAL_FULL_TEMPLATE_GGUF_TOKENS_STORED_QUERY_VECTORS_NOT_WEIGHT_INFERENCE'))
            for label in RUNTIME_CASES:
                case=next(c for c in reference['cases'] if c['id']==label);registry=SessionRegistry()
                for name in case['packs']:registry.activate(packs[name])
                before=generator.calls;result=PackRAG(registry,encoder,generator).answer(Query(case['raw'],case['as_of']))
                save(run/(label+'-observed.json'),dict(id=label,status='OBSERVED_NOT_ACCEPTANCE',result=result,
                    generate_calls_for_case=generator.calls-before,diagnostic_final_candidate_not_product_answer=generator.last_final_candidate if generator.calls>before else None))
                assert result['state']==case['expected_state'],label
                if case['expected_state']=='NO_RELEVANT_EVIDENCE':
                    assert generator.calls==before and not result['selected'] and result['answer'] is None
                else:
                    assert generator.calls==before+1 and '74 °C' in result['answer'] and result['sources']
                    assert '</think>' not in result['answer']
                item=dict(id=label,status='PASS',result=result,generate_calls_for_case=generator.calls-before,
                    actual_weight_inference=case['expected_state']=='ANSWER_ACCEPTED',model_load_not_excluded=True)
                results.append(item);save(run/(label+'.json'),item);print(label,result['state'],'PASS',flush=True)
        status='PASS'
    except Exception:
        (run/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        save(run/'relevance-smoke-results.json',dict(status=status,cases=results,tokenizer_cases=len(tokens),
            purpose='REAL_LFM_SYNTHETIC_GATE_NOT_MEASURED_CALIBRATION_RELEASE_GOLD_OR_PERFORMANCE',raw_reasoning_persisted=False))
        save(run/'output-hashes.json',{p.relative_to(run).as_posix():file_sha(p) for p in run.rglob('*') if p.is_file() and p.name!='output-hashes.json'})

if __name__=='__main__':main()
