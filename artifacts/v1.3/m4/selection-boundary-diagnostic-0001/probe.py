"""Read-only exact-boundary diagnosis; actual vocabulary, no generation/pack creation."""
import html
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.v13_smoke import owned_server,save
from scripts.v13_selection_fixtures import EN

run=Path(__file__).parent
def block(value):return '<SOURCE id="S1" pack="org.packrag.contract.boundary1200@1.0.0" title="SYNTHETIC BUDGET" locator="thermal">\n'+html.escape(value,quote=False)+'\n</SOURCE>'
records=[]
with owned_server(run) as tokenizer:
    base=len(tokenizer.tokenize(block(EN),add_special=False));guess=1200-base
    for count in (0,1,2,10,guess,guess-1,guess+1):
        text=block(EN+' pad'*count);tokens=tokenizer.tokenize(text,add_special=False)
        records.append(dict(padding_count=count,evidence_tokens=len(tokens),first_tokens=tokens[:12],last_tokens=tokens[-12:]))
        save(run/'observations.json',dict(scope='ACTUAL_FULL_XML_COUNTS_NO_GENERATION_OR_PACK_CREATION',base=base,target=1200,records=records))
    print('Full XML observed:',[(row['padding_count'],row['evidence_tokens']) for row in records],flush=True)
