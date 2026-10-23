"""Owner-authorized profile revision; exact frozen repair inputs, no product promotion."""
import json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from product.packrag.config import file_sha
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack,SessionRegistry
from product.packrag.runtime import PackRAG
from product.packrag.retrieval import Query
import product.packrag.prompt as prompt
import product.packrag.evidence as evidence
from scripts.v13_smoke import owned_server,save
HERE=Path(__file__).resolve().parent;RUN=ROOT/'artifacts/v1.3/m4/repair-guide-revision-desktop-0001'
RUN.mkdir(exist_ok=False)
policy=HERE/'guide-policy-candidate-0001.txt';gold=HERE/'repair-cases-frozen-0001.json'
files=[Path(__file__),policy,gold,HERE/'repair-documents-frozen-0001.json',ROOT/'product/config/runtime-profile.json',ROOT/'product/packrag/generator.py']
hashes={str(p.relative_to(ROOT)):file_sha(p) for p in files}
baseline=evidence.PROFILE.copy();candidate=baseline.copy();candidate.update(profile_id='mobile-v1-guides-rc1',generated_tokens_cap=1024)
original_system=prompt.SYSTEM;candidate_system=original_system+'\n'+policy.read_text().strip()
save(RUN/'inputs.json',dict(status='OWNER_AUTHORIZED_CANDIDATE_NOT_PRODUCT_PROMOTION',started_utc=datetime.now(timezone.utc).isoformat(),
    sha256=hashes,baseline_profile=baseline,candidate_profile=candidate,original_system=original_system,candidate_system=candidate_system,
    scope='Same frozen questions/gold/documents/trust/model/template/embedder/selection/context/sampling/validators; two explicit changes: generated ceiling and appended general output instructions. No per-question tuning.'))
evidence.PROFILE=candidate;prompt.SYSTEM=candidate_system
encoder=GraniteEncoder(ROOT/'models/v1.3/granite');prep=ROOT/'artifacts/v1.3/m4/repair-skills-prepared-0001'
results=[]
with VerifiedPack(prep/'repair-skills.kpack',[(prep/'public-key.raw').read_bytes()],developer_mode=True) as pack,owned_server(RUN) as generator:
    registry=SessionRegistry();registry.activate(pack);runtime=PackRAG(registry,encoder,generator)
    for case in json.loads(gold.read_text())['cases']:
        result=runtime.answer(Query(case['question'],case['as_of']))
        final=(result['answer'] or '').casefold()
        row=dict(id=case['id'],expected_state=case['expected_state'],state_matches=result['state']==case['expected_state'],result=result,
            missing_lexical_concepts=[v for v in case['required_concepts'] if v.casefold() not in final],
            possible_unsupported_phrases=[v for v in case['unsupported_concepts'] if v.casefold() in final],
            scope='GUIDES_RC1_NOT_PRODUCT_PROMOTION_MANUAL_ENTAILMENT_AND_ORDER_REVIEW_REQUIRED')
        save(RUN/(case['id']+'.json'),row);results.append(row)
        save(RUN/'progress.json',dict(completed=[r['id'] for r in results],status='RUNNING_CANDIDATE_NOT_ACCEPTANCE'))
        print(case['id'],result['state'],result.get('rejection_reason'),result.get('timings',{}).get('generation',{}).get('emitted_token_count'),flush=True)
for name,digest in hashes.items():assert file_sha(ROOT/name)==digest
save(RUN/'results.json',dict(status='COMPLETE_CANDIDATE_MANUAL_REVIEW_REQUIRED',cases=results,hidden_reasoning_saved=False))
