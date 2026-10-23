"""Independent XML construction from architecture and fixed source specifications."""
import hashlib,json,html,traceback
from pathlib import Path
from datetime import datetime,timezone
from scripts.v13_smoke import owned_server,save
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;M4=ROOT/'artifacts/v1.3/m4'
assert not (HERE/'oracle.json').exists()
reference=json.loads((M4/'representation-fixtures-0001/cases.json').read_text())
specs={r['id']:r for r in json.loads((M4/'representation-fixtures-0001/source-specifications.json').read_text())['valid']}
observed={r['id']:r for r in json.loads((M4/'representation-smoke-0002/tokenizer-cases.json').read_text())['cases']}
architecture=json.loads((ROOT/'artifacts/v1.3/architecture/paragraphs.json').read_text())
paragraph=next(r['text'] for r in architecture if r['index']==548)
system=paragraph.split('SYSTEM ROLE (actual chat-template system message):\n',1)[1].split('\n\nUSER ROLE:',1)[0]
results=[];status='FAIL'
try:
    with owned_server(HERE) as tokenizer:
        for label,index in [('en-canonical',None),('fr-official',0),('ar-reviewed',0),('fr-reviewed',0),('regional',0),('preferred',1),('xml-data',0)]:
            spec=specs[label];case=next(c for c in reference['cases'] if c['id']==label)
            pack_id,version,_=case['candidates'][0]['origins'][0]
            body=spec['text'] if index is None else spec['derived'][index]['text']
            title=spec.get('title','Aster-9');assert title=='Aster-9'
            # Fixture attributes contain no escaping characters; body and question
            # use Python's standard HTML escape, independent of product Prompt.
            source=f'<SOURCE id="S1" pack="{pack_id}@{version}" title="{title}" locator="thermal">\n{html.escape(body,quote=False)}\n</SOURCE>'
            prefix=f'<QUESTION>\n{html.escape(case["raw"],quote=False)}\n</QUESTION>\n\n<CONTEXT>\nas_of_date={case["as_of"]}\nactive_packs={pack_id}@{version}\n</CONTEXT>\n\n<VERIFIED_EVIDENCE>\n'
            user=prefix+source+'\n</VERIFIED_EVIDENCE>';empty_user=prefix+'\n</VERIFIED_EVIDENCE>'
            actual=tokenizer.render_tokens(system,user);evidence=len(tokenizer.tokenize(source,add_special=False))
            expected=observed[label];assert expected['admission']=='READY'
            assert actual==expected['actual_tokenizer']['tokens'] and evidence==expected['actual_tokenizer']['evidence_tokens']
            assert len(actual)==expected['actual_tokenizer']['prefill_tokens']
            assert min(512,2048-len(actual))==expected['actual_tokenizer']['max_new']
            assert evidence<=min(1200,1536-len(tokenizer.render_tokens(system,empty_user))) and len(actual)<=1536
            if spec['language']!='en':assert spec['text'] not in user
            results.append(dict(id=label,status='PASS',prefill_tokens=len(actual),evidence_tokens=evidence,
                rendered_body_sha256=hashlib.sha256(body.encode()).hexdigest(),source=source,user=user,
                system_sha256=hashlib.sha256(system.encode()).hexdigest(),tokens=actual))
    status='PASS'
except Exception:
    (HERE/'failure.txt').write_text(traceback.format_exc());raise
finally:
    save(HERE/'oracle.json',dict(status=status,recorded_utc=datetime.now(timezone.utc).isoformat(),cases=results,
        purpose='INDEPENDENT_ARCHITECTURE_XML_AND_FIXED_BODY_ACTUAL_GGUF_TOKEN_BUDGETS_NOT_GENERATION_OR_REAL_REVIEW',raw_reasoning_persisted=False))
    save(HERE/'output-hashes.json',{p.relative_to(HERE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file() and p.name!='output-hashes.json'})
print('Independent frozen XML/English representation actual token oracle PASS:',len(results))
