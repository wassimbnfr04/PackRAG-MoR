import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from product.packrag.config import file_sha
from product.packrag.generation_policy import QUOTES,QUOTE_CONFIG_SHA,quote_units,quote_grammar
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack
from product.packrag.retrieval import Query,retrieve
from product.packrag.prompt import prepare,SYSTEM,user_message
from scripts.v13_smoke import save
from owned_product_quotes_server_0001 import owned_server
HERE=Path(__file__).resolve().parent;RUN=ROOT/'artifacts/v1.3/m4/quote-native-parity-prepared-0001';RUN.mkdir(exist_ok=False)
case=next(row for row in json.loads((HERE/'repair-cases-frozen-0001.json').read_text())['cases'] if row['id']=='FAN_FULL_GUIDE')
query=Query(case['question'],case['as_of']);encoder=GraniteEncoder(ROOT/'models/v1.3/granite');packroot=ROOT/'artifacts/v1.3/m4/repair-skills-prepared-0001'
with VerifiedPack(packroot/'repair-skills.kpack',[(packroot/'public-key.raw').read_bytes()],developer_mode=True) as pack,owned_server(RUN) as generator:
 candidates,ambiguous=retrieve((pack,),query,encoder.encode(query.normalized));assert not ambiguous
 prompt=prepare(query,(pack.identity,),candidates,generator,QUOTES)
 units=quote_units(row.text for row in prompt.representations)
 row=dict(scope='ACTUAL_PINNED_DESKTOP_TOKENIZER_AND_RENDERING_NOT_GENERATION_OR_NATIVE_ACCEPTANCE',question=query.raw,as_of=query.as_of,system=QUOTES.system(SYSTEM),user=user_message(query,(pack.identity,),list(prompt.evidence)),tokens=list(prompt.tokens),maximum=prompt.max_new_tokens,units=units,grammar=quote_grammar(units),closing_token=generator.tokenize('</think>',add_special=False)[0],config_sha256=QUOTE_CONFIG_SHA,generator=generator.metadata)
 save(RUN/'parity.json',row)
 print('ACTUAL_DESKTOP_TOKENIZER_PARITY_REFERENCE_READY',len(prompt.tokens),flush=True)
