"""Explicit ADR004 policy experiment, not product or literal-v1.3 acceptance."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from product.packrag.config import file_sha
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack,SessionRegistry
from product.packrag.runtime import PackRAG
from product.packrag.retrieval import Query
import product.packrag.prompt as prompt
from scripts.v13_smoke import owned_server,save
HERE=Path(__file__).resolve().parent;RUN=ROOT/'artifacts/v1.3/m4/repair-compact-pilot-0001'
RUN.mkdir(exist_ok=False)
candidate=HERE/'compact-policy-candidate-0001.txt';gold=HERE/'repair-cases-frozen-0001.json'
inputs=[Path(__file__),candidate,gold,HERE/'repair-documents-frozen-0001.json',ROOT/'product/packrag/generator.py']
hashes={str(p.relative_to(ROOT)):file_sha(p) for p in inputs}
original=prompt.SYSTEM;prompt.SYSTEM=original+'\n'+candidate.read_text().strip()
save(RUN/'inputs.json',dict(status='EXPERIMENTAL_POLICY_NOT_PRODUCT',sha256=hashes,original_system=original,experimental_system=prompt.SYSTEM,
    unchanged='Raw questions, evidence, model, official template, sampling,512 cap,2048 context, selection/citation validators'))
encoder=GraniteEncoder(ROOT/'models/v1.3/granite');prep=ROOT/'artifacts/v1.3/m4/repair-skills-prepared-0001'
results=[]
with VerifiedPack(prep/'repair-skills.kpack',[(prep/'public-key.raw').read_bytes()],developer_mode=True) as pack,owned_server(RUN) as generator:
    registry=SessionRegistry();registry.activate(pack);runtime=PackRAG(registry,encoder,generator)
    for case in json.loads(gold.read_text())['cases']:
        if case['id'] not in ('FAN_FULL_GUIDE','FAN_CLEANING_TOOLS','TUBE_FULL_GUIDE'):continue
        result=runtime.answer(Query(case['question'],case['as_of']))
        row=dict(id=case['id'],result=result,scope='ADR004_FORMAT_PILOT_NOT_PRODUCT_ACCEPTANCE')
        save(RUN/(case['id']+'.json'),row);results.append(row)
        print(case['id'],result['state'],result.get('rejection_reason'),result.get('timings',{}).get('generation',{}).get('emitted_token_count'),flush=True)
for name,digest in hashes.items():assert file_sha(ROOT/name)==digest
save(RUN/'results.json',dict(status='COMPLETE_PILOT_MANUAL_ENTAILMENT_REVIEW_REQUIRED',cases=results,hidden_reasoning_saved=False))
