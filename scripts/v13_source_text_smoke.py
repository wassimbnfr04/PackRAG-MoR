"""Signed presence imports and real full-template tokenizer; no weight inference."""
import argparse,json,traceback
from contextlib import ExitStack
from dataclasses import asdict
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from kpack_builder.core import PackError
from product.packrag.config import file_sha
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack
from product.packrag.prompt import prepare
from product.packrag.retrieval import Query,retrieve
from scripts.v13_result_manifest import public_source_files
from scripts.v13_smoke import ROOT,owned_server,save

CORPUS=ROOT/'artifacts/v1.3/m4/source-text-fixtures-0001'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT);run.mkdir(parents=True,exist_ok=False)
    save(run/'inputs.json',dict(started_utc=datetime.now(timezone.utc).isoformat(),source_sha256={p.relative_to(ROOT).as_posix():file_sha(p) for p in public_source_files(ROOT)},corpus_sha256=file_sha(CORPUS/'cases.json')))
    imports=[];tokens=[];status='FAIL'
    try:
        reference=json.loads((CORPUS/'cases.json').read_text());public=(CORPUS/'public-key.raw').read_bytes();assert file_sha(CORPUS/'public-key.raw')==reference['public_key_sha256']
        encoder=GraniteEncoder(ROOT/'models/v1.3/granite');query=Query(reference['raw'],reference['as_of']);vector=encoder.encode(query.normalized)
        assert query.normalized==reference['normalized'];max_embedding=float(np.max(np.abs(vector-np.asarray(reference['query_vector'],dtype=np.float32))));assert max_embedding<=1e-4
        with ExitStack() as stack,owned_server(run) as backend:
            for row in reference['packs']:
                path=CORPUS/row['filename'];assert file_sha(path)==row['sha256']
                try:pack=stack.enter_context(VerifiedPack(path,[public],developer_mode=True))
                except PackError as error:
                    observation=dict(id=row['id'],accepted=False,error=type(error).__name__+': '+str(error));save(run/(row['id']+'-import-observed.json'),observation);assert not row['accept'];imports.append(observation);continue
                observation=dict(id=row['id'],accepted=True,error=None);save(run/(row['id']+'-import-observed.json'),observation);assert row['accept'];imports.append(observation)
                candidates,ambiguous=retrieve((pack,),query,vector);assert not ambiguous and len(candidates)==1 and candidates[0].exact and candidates[0].relevant
                candidate=candidates[0];assert candidate.chunk['canonical_text']==row['canonical_text'] and candidate.chunk['text_sha256']==row['canonical_text_sha256'] and candidate.chunk['language']=='fr'
                prompt=prepare(query,(pack.identity,),candidates,backend)
                record=dict(id=row['id'],status='OBSERVED_NOT_ACCEPTANCE',admission='READY',max_embedding_abs_error=max_embedding,
                    actual_tokenizer=dict(tokens=list(prompt.tokens),prefill_tokens=prompt.prefill_tokens,evidence_tokens=prompt.evidence_tokens,max_new=prompt.max_new_tokens,selected=[c.chunk['chunk_id'] for c in prompt.evidence]),
                    representations=[asdict(r) for r in prompt.representations],canonical_text=candidate.chunk['canonical_text'],canonical_text_sha256=candidate.chunk['text_sha256'])
                save(run/(row['id']+'-tokenizer-observed.json'),record);assert record['representations']==[row['generator_representation']]
                assert prompt.prefill_tokens<=1536 and prompt.evidence_tokens<=1200 and len(prompt.evidence)==1 and prompt.max_new_tokens<=512
                record['status']='PASS';tokens.append(record);print(row['id'],'signed import/preserved provenance/actual tokenizer PASS',flush=True)
        assert len(imports)==6 and sum(r['accepted'] for r in imports)==2 and len(tokens)==2;status='PASS'
    except Exception:
        (run/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        save(run/'source-text-smoke-results.json',dict(status=status,imports=imports,tokenizer_cases=tokens,purpose='SIGNED_PRESENCE_BYTE_PRESERVATION_ACTUAL_GRANITE_GGUF_TOKENIZER_NOT_WEIGHT_INFERENCE_OR_REAL_REVIEW'))
        save(run/'output-hashes.json',{p.relative_to(run).as_posix():file_sha(p) for p in run.rglob('*') if p.is_file() and p.name!='output-hashes.json'})

if __name__=='__main__':main()
