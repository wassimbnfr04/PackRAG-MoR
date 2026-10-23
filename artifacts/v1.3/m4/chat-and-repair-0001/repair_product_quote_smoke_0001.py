import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from product.packrag.config import file_sha
from product.packrag.generation_policy import QUOTES
from product.packrag.runtime import PackRAG
from product.packrag.packs import SessionRegistry
from product.packrag.retrieval import Query
from scripts.v13_smoke import save
OLD=ROOT/'artifacts/v1.3/m4/product-quote-smoke-0001';RUN=ROOT/'artifacts/v1.3/m4/product-quote-smoke-retention-0001';RUN.mkdir(exist_ok=False)
inputs=json.loads((OLD/'inputs.json').read_text());assert all(file_sha(ROOT/name)==value for name,value in inputs.items())
assert json.loads((OLD/'server-stop.json').read_text())['returncode']==0
for name,state in [('FAN_FULL_GUIDE','ANSWER_ACCEPTED'),('TUBE_UNDOCUMENTED_PRESSURE','INSUFFICIENT_EVIDENCE')]:
 row=json.loads((OLD/(name+'.json')).read_text());assert row['state']==state
 if state=='ANSWER_ACCEPTED':assert row['answer']=='1. '+row['sources'][0]['generator_representation']['text']+' [S1]'
class NoCalls:
 metadata={'scope':'MOCK_NO_ACTIVE_SNAPSHOT_CONTROL_NO_WEIGHT_INFERENCE'}
 def encode(self,*args):raise AssertionError('No encoder call allowed')
 def generate(self,*args):raise AssertionError('No generation call allowed')
registry=SessionRegistry();control=PackRAG(registry,NoCalls(),NoCalls(),QUOTES).answer(Query('How do I clean the Framework Laptop 12 fan?','2026-10-12'))
assert control['state']=='NO_ACTIVE_PACK';save(RUN/'empty-snapshot-control.json',control)
save(RUN/'result.json',dict(status='PASS_RETAINED_REAL_PRODUCTION_DESKTOP_QUOTE_SMOKE_PLUS_MOCK_EMPTY_SNAPSHOT_CONTROL',original_real_outputs={name:file_sha(OLD/name) for name in ['FAN_FULL_GUIDE.json','TUBE_UNDOCUMENTED_PRESSURE.json','before-import.json','server-stop.json']},input_source_hashes=inputs,inputs_unchanged=True,repair='Original helper erroneously called deactivate on session-only registry, which has no lifecycle API. Preserve original harness failure; retain successful actual model queries after verifying hashes. Fresh empty-snapshot control is explicitly mock, not lifecycle deactivation or weight inference. Existing physical/U2 lifecycle evidence remains separate.',no_actual_model_rerun=True))
print('PASS_RETAINED_REAL_SMOKE_PLUS_MOCK_EMPTY_CONTROL',flush=True)
