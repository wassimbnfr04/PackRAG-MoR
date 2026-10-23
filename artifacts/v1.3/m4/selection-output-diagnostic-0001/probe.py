"""Changed user formatting request, unchanged source/model/policy/validator.

Observation only. Introduced after an uncited introductory paragraph failure;
cannot be claimed as an independently held-out supported-answer result.
"""
from contextlib import ExitStack
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from product.packrag.config import file_sha
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack,SessionRegistry
from product.packrag.retrieval import Query
from product.packrag.runtime import PackRAG
from scripts.v13_conflict_smoke import CountingBackend
from scripts.v13_selection_smoke import CORPUS
from scripts.v13_result_manifest import public_source_files
from scripts.v13_smoke import owned_server,save

run=Path(__file__).parent
ref=json.loads((CORPUS/'cases.json').read_text());case=next(row for row in ref['cases'] if row['id']=='atomic-last')
pack_record=next(row for row in ref['packs'] if row['id']=='atomic-last')
question=case['raw']+' Answer in one factual paragraph; cite the sources used.'
save(run/'inputs.json',dict(recorded_utc=datetime.now(timezone.utc).isoformat(),original_question=case['raw'],diagnostic_question=question,
    unchanged_pack_sha256=file_sha(CORPUS/pack_record['filename']),source_sha256={p.relative_to(ROOT).as_posix():file_sha(p) for p in public_source_files(ROOT)},
    scope='FORMAT_CONTROL_AFTER_UNCITED_HEADER_FAILURE_NOT_HELDOUT_NOT_ACCEPTANCE'))
encoder=GraniteEncoder(ROOT/'models/v1.3/granite')
with VerifiedPack(CORPUS/pack_record['filename'],[(CORPUS/'public-key.raw').read_bytes()],developer_mode=True) as pack,owned_server(run) as backend:
    registry=SessionRegistry();registry.activate(pack);generator=CountingBackend(backend)
    query=Query(question,case['as_of'],case['jurisdiction']);vector=encoder.encode(query.normalized)
    result=PackRAG(registry,encoder,generator).answer(query)
    save(run/'observed.json',dict(status='OBSERVATION_ONLY_NOT_ACCEPTANCE',result=result,query_vector=vector.tolist(),
        generation_calls=generator.calls,diagnostic_final_candidate_not_product_answer=generator.last_final_candidate))
    print(result['state'],result.get('rejection_reason'),[(row['chunk_id'],row['fused_rank']) for row in result['selected']],flush=True)
