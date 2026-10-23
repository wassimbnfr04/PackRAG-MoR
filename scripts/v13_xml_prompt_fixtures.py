"""New actual-token references for frozen v1.3 XML roles; originals stay immutable."""
import argparse
import json
import shutil
import traceback
from pathlib import Path
from datetime import datetime, timezone
from product.packrag.config import file_sha
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack
from product.packrag.prompt import prepare, SYSTEM, user_message
from product.packrag.retrieval import Query, retrieve
from scripts.v13_smoke import ROOT, owned_server, save


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT);run.mkdir(parents=True,exist_ok=False)
    source=ROOT/'product/android/app/src/androidTest/assets';old_path=source/'parity-reference.json'
    old=json.loads(old_path.read_text());target=source/'prompt-v13-xml-corpus';assert not target.exists()
    pack_path=source/'walking-skeleton.kpack';assert file_sha(pack_path)==old['developer_pack_sha256']
    before={path.name:file_sha(path) for path in (old_path,pack_path,source/'developer-public-key.raw')}
    paragraphs=json.loads((ROOT/'artifacts/v1.3/architecture/paragraphs.json').read_text())
    paragraph=next(row['text'] for row in paragraphs if row['index']==548)
    status='FAIL';cases=[]
    try:
        encoder=GraniteEncoder(ROOT/'models/v1.3/granite')
        with VerifiedPack(pack_path,[(source/'developer-public-key.raw').read_bytes()],developer_mode=True) as pack,owned_server(run) as generator:
            for original in old['prompt_cases']:
                query=Query(original['query'],original['as_of']);vector=encoder.encode(query.normalized)
                candidates,ambiguous=retrieve((pack,),query,vector);assert not ambiguous
                prepared=prepare(query,(pack.identity,),candidates,generator)
                assert SYSTEM==original['system']
                cases.append(dict(id=original['id'],query=query.raw,as_of=query.as_of,normalized_embedding_input=query.normalized,
                    system=SYSTEM,user=user_message(query,(pack.identity,),list(prepared.evidence)),tokens=list(prepared.tokens),
                    prefill=prepared.prefill_tokens,evidence_tokens=prepared.evidence_tokens,max_new=prepared.max_new_tokens,
                    selected=[item.chunk['chunk_id'] for item in prepared.evidence],
                    candidate_order=[item.chunk['chunk_id'] for item in candidates],
                    sparse_ranks=[item.sparse_rank for item in candidates],dense_ranks=[item.dense_rank for item in candidates],
                    rrf=[item.rrf for item in candidates],dense_cosines=[item.dense_cosine for item in candidates]))
        assert len(cases)==10
        assert before=={path.name:file_sha(path) for path in (old_path,pack_path,source/'developer-public-key.raw')}
        record=dict(status='ACTUAL_XML_TOKEN_REFERENCES_NOT_GENERATION_OR_DEVICE_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
            script_sha256=file_sha(Path(__file__)),original_assets_sha256=before,developer_pack_sha256=file_sha(pack_path),
            architecture_sha256=file_sha(ROOT/'artifacts/v1.3/architecture/architecture-v1.3.docx'),
            paragraph548_sha256=__import__('hashlib').sha256(paragraph.encode()).hexdigest(),
            prompt_serialization='V1.3_XML_ENVELOPE',policy_text_unchanged=True,prompt_cases=cases,
            embedding_note='Actual normalized query vectors, matching product runtime since B2. Older retained tokenizer fixture used raw-query vectors; it is preserved, not relabeled.',
            generator_note='Actual pinned GGUF tokenizer/official template on owned WSL server; no completion requested',private_keys_included=False)
        save(run/'prompt-reference.json',record);target.mkdir();shutil.copyfile(run/'prompt-reference.json',target/'prompt-reference.json');status='PASS'
    except Exception:
        (run/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:save(run/'fixture-result.json',dict(status=status,cases=len(cases)))
    print('Frozen10 new actual normalized-query XML/official-template token references; prior assets unchanged')


if __name__=='__main__':main()
