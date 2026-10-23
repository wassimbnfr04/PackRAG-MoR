import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from product.packrag.config import file_sha
from product.packrag.generation_policy import QUOTES
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack,SessionRegistry
from product.packrag.runtime import PackRAG
from product.packrag.retrieval import Query
from scripts.v13_smoke import save
from owned_product_quotes_server_0001 import owned_server
HERE=Path(__file__).resolve().parent;RUN=ROOT/'artifacts/v1.3/m4/product-quote-smoke-0001';RUN.mkdir(exist_ok=False)
files=[ROOT/('product/packrag/'+name+'.py') for name in ['generation_policy','generator','runtime','prompt','evidence','output']]+[ROOT/'product/config/generation-profile-quotes-v1.json',Path(__file__),HERE/'owned_product_quotes_server_0001.py',HERE/'repair-cases-frozen-0001.json']
inputs={str(p.relative_to(ROOT)):file_sha(p) for p in files};save(RUN/'inputs.json',inputs)
encoder=GraniteEncoder(ROOT/'models/v1.3/granite');prepared=ROOT/'artifacts/v1.3/m4/repair-skills-prepared-0001'
with VerifiedPack(prepared/'repair-skills.kpack',[(prepared/'public-key.raw').read_bytes()],developer_mode=True) as pack,owned_server(RUN) as generator:
 registry=SessionRegistry();runtime=PackRAG(registry,encoder,generator,QUOTES)
 before=runtime.answer(Query('How do I clean the Framework Laptop 12 fan?','2026-10-12'));assert before['state']=='NO_ACTIVE_PACK';save(RUN/'before-import.json',before)
 registry.activate(pack)
 for case in json.loads((HERE/'repair-cases-frozen-0001.json').read_text())['cases']:
  if case['id'] not in ('FAN_FULL_GUIDE','TUBE_UNDOCUMENTED_PRESSURE'):continue
  result=runtime.answer(Query(case['question'],case['as_of']));save(RUN/(case['id']+'.json'),result)
  print(case['id'],result['state'],flush=True);assert result['state']==case['expected_state']
  if result['state']=='ANSWER_ACCEPTED':assert result['answer']=='1. '+result['sources'][0]['generator_representation']['text']+' [S1]'
 registry.deactivate(pack.identity[0]);after=runtime.answer(Query('How do I clean the Framework Laptop 12 fan?','2026-10-12'));assert after['state']=='NO_ACTIVE_PACK';save(RUN/'after-deactivation.json',after)
for name,digest in inputs.items():assert file_sha(ROOT/name)==digest
save(RUN/'result.json',dict(status='PASS_REAL_PRODUCTION_DESKTOP_QUOTE_WALKING_SMOKE_NOT_NATIVE_OR_M4',no_global_profile_or_system_mutation=True,hidden_reasoning_saved=False,inputs_unchanged=True))
