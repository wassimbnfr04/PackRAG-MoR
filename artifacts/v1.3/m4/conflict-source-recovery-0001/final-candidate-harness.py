"""Owned real LFM conflict smoke and exact full-template tokenizer evidence.

Synthetic source facts are fixed, not release legal gold or calibration.
Never persists the generated raw reasoning buffer or overwrites prior runs.
"""
import argparse
import json
import traceback
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from product.packrag.config import RuntimeContractError, file_sha
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack, SessionRegistry
from product.packrag.prompt import prepare, SYSTEM, user_message
from product.packrag.retrieval import Query, retrieve
from product.packrag.runtime import PackRAG
from scripts.v13_result_manifest import public_source_files
from scripts.v13_smoke import ROOT, owned_server, save

CORPUS=ROOT/'artifacts/v1.3/m4/conflict-fixtures-0001'


class CountingBackend:
    def __init__(self,backend):self.backend=backend;self.calls=0;self.last_final_candidate=None
    def __getattr__(self,name):return getattr(self.backend,name)
    def generate(self,prompt):
        self.calls+=1
        generated=self.backend.generate(prompt)
        # Research diagnostic only: completed final candidate, never hidden reasoning
        # and never exposed as a product answer before output validation.
        self.last_final_candidate=generated.buffer.split('</think>',1)[1].strip() if generated.buffer.count('</think>')==1 else None
        return generated


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--case-id',choices=('UNKNOWN','DIFFERENT_CURATORS','BEFORE_CAP','FIVE_COMPANIONS','AUTHORITY','SUPERSEDES_CURRENT','EXCEPTION'))
    args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT);run.mkdir(parents=True,exist_ok=False)
    save(run/'inputs.json',dict(started_utc=datetime.now(timezone.utc).isoformat(),selected_case=args.case_id,
        source_sha256={path.relative_to(ROOT).as_posix():file_sha(path) for path in public_source_files(ROOT)},
        corpus_sha256=file_sha(CORPUS/'cases.json')))
    status='FAIL';results=[];token_cases=[]
    try:
        reference=json.loads((CORPUS/'cases.json').read_text());encoder=GraniteEncoder(ROOT/'models/v1.3/granite')
        public=[]
        for row in reference['public_keys']:
            path=CORPUS/row['filename'];assert file_sha(path)==row['sha256'];public.append(path.read_bytes())
        with ExitStack() as stack,owned_server(run) as backend:
            packs={}
            for row in reference['packs']:
                path=CORPUS/row['filename'];assert file_sha(path)==row['sha256']
                packs[row['id']]=stack.enter_context(VerifiedPack(path,public,developer_mode=True))
            generator=CountingBackend(backend)
            for case in reference['cases']:
                query=Query(case['raw'],case['as_of'],case['jurisdiction'],case['current_law'])
                active=tuple(packs[name] for name in case['packs'])
                candidates,ambiguous=retrieve(active,query,np.asarray(case['query_vector'],dtype=np.float32))
                admission='IDENTIFIER_AMBIGUOUS';tokens={}
                if not ambiguous:
                    if not any(item.relevant for item in candidates):admission='NO_RELEVANT_EVIDENCE'
                    else:
                        try:
                            prepared=prepare(query,tuple(pack.identity for pack in active),candidates,generator)
                            admission='READY';tokens=dict(tokens=list(prepared.tokens),prefill_tokens=prepared.prefill_tokens,
                                evidence_tokens=prepared.evidence_tokens,max_new=prepared.max_new_tokens,
                                selected=[item.chunk['chunk_id'] for item in prepared.evidence])
                            assert prepared.prefill_tokens<=1536 and prepared.evidence_tokens<=1200 and len(prepared.evidence)<=4 and prepared.max_new_tokens<=512
                        except RuntimeContractError as error:admission=str(error)
                elif case['id']=='UNKNOWN':
                    try:prepare(query,tuple(pack.identity for pack in active),candidates,generator)
                    except RuntimeContractError as error:assert str(error)=='LEGAL_CONFLICT_UNRESOLVED'
                    else:raise AssertionError('Unresolved selected conflict entered prompt')
                expected='INCOMPLETE_LEGAL_CONFLICT_EVIDENCE' if case['id']=='FIVE_COMPANIONS' else ('IDENTIFIER_AMBIGUOUS' if ambiguous else ('READY' if candidates else 'NO_RELEVANT_EVIDENCE'))
                assert admission==expected,case['id']
                token_cases.append(dict(id=case['id'],status='PASS',admission=admission,actual_tokenizer=tokens))
            save(run/'tokenizer-cases.json',dict(status='PASS',cases=token_cases,
                purpose='ACTUAL_GGUF_FULL_TEMPLATE_TOKENS_USING_FROZEN_ACTUAL_QUERY_VECTORS_NOT_WEIGHT_INFERENCE'))
            for identity in ('UNKNOWN','DIFFERENT_CURATORS','BEFORE_CAP','FIVE_COMPANIONS','AUTHORITY','SUPERSEDES_CURRENT','EXCEPTION'):
                if args.case_id is not None and identity!=args.case_id:continue
                case=next(row for row in reference['cases'] if row['id']==identity);registry=SessionRegistry()
                for name in case['packs']:registry.activate(packs[name])
                runtime=PackRAG(registry,encoder,generator);before=generator.calls
                result=runtime.answer(Query(case['raw'],case['as_of'],case['jurisdiction']))
                guarded=identity in ('UNKNOWN','DIFFERENT_CURATORS','BEFORE_CAP','FIVE_COMPANIONS')
                save(run/(identity+'-observed.json'),dict(id=identity,status='OBSERVED_NOT_ACCEPTANCE',
                    generate_calls_for_case=generator.calls-before,result=result,
                    diagnostic_final_candidate_not_product_answer=generator.last_final_candidate if generator.calls>before else None))
                if guarded:
                    expected='INCOMPLETE_LEGAL_CONFLICT_EVIDENCE' if identity=='FIVE_COMPANIONS' else 'IDENTIFIER_AMBIGUOUS'
                    assert result['state']==expected and result['answer'] is None and generator.calls==before and not result['selected'],identity
                else:
                    assert result['state']=='ANSWER_ACCEPTED' and '74 °C' in result['answer'] and '68 °C' not in result['answer'],identity
                    assert generator.calls==before+1 and '</think>' not in result['answer']
                    assert len(result['selected'])==(2 if identity=='EXCEPTION' else 1)
                    assert any(source['canonical_text']=='The Aster-9 thermal controller has a maximum continuous operating temperature of 74 °C.' for source in result['sources'])
                    assert all(source['conflicts'] and all(c['state']!='UNRESOLVED' for c in source['conflicts']) for source in result['sources'])
                item=dict(id=identity,status='PASS',actual_weight_inference=not guarded,model_load_not_excluded=guarded,
                    generate_calls_for_case=generator.calls-before,result=result)
                results.append(item);save(run/(identity+'.json'),item);print(identity,result['state'],'PASS',flush=True)
        status='PASS'
    except Exception:
        (run/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        save(run/'conflict-smoke-results.json',dict(status=status,cases=results,tokenizer_cases=len(token_cases),
            purpose='REAL_LFM_SYNTHETIC_CONFLICT_INTEGRATION_NOT_RELEASE_LEGAL_REVIEW_CALIBRATION_OR_PERFORMANCE',raw_reasoning_persisted=False))
        save(run/'output-hashes.json',{path.relative_to(run).as_posix():file_sha(path) for path in run.rglob('*') if path.is_file() and path.name!='output-hashes.json'})


if __name__=='__main__':main()
