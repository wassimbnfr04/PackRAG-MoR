"""Owner-authorized decoder-format prototype; never product promotion."""
import json,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from product.packrag.config import file_sha
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack,SessionRegistry
from product.packrag.runtime import PackRAG
from product.packrag.retrieval import Query
from product.packrag.output import validate_output
from types import SimpleNamespace
import product.packrag.prompt as prompt
import product.packrag.evidence as evidence
from scripts.v13_smoke import owned_server,save
HERE=Path(__file__).resolve().parent;RUN=ROOT/'artifacts/v1.3/m4/repair-guide-preservation-pilot-0004';RUN.mkdir(exist_ok=False)
policy=HERE/'guide-policy-candidate-0004.txt';gold=HERE/'repair-cases-frozen-0001.json'
files=[Path(__file__),policy,gold,HERE/'repair-documents-frozen-0001.json',ROOT/'product/config/runtime-profile.json',ROOT/'product/packrag/generator.py']
hashes={str(p.relative_to(ROOT)):file_sha(p) for p in files}
baseline=evidence.PROFILE.copy();candidate=baseline.copy();candidate.update(profile_id='mobile-v1-guides-rc9',generated_tokens_cap=1024)
evidence.PROFILE.update(candidate);original_system=prompt.SYSTEM;prompt.SYSTEM=original_system+'\n'+policy.read_text().strip()
trigger='</think>'
def grammar(ids):
    assert 1<=len(ids)<=4 and ids==['S'+str(i) for i in range(1,len(ids)+1)]
    return '\n'.join([
        'root ::= "</think>" pad ("INSUFFICIENT_EVIDENCE" | line (sep line)*) pad',
        'line ::= text " " citations continuation* "."?',
        'continuation ::= "."? " " text " " citations',
        'citations ::= cite (" " cite)? (" " cite)? (" " cite)?',
        r'text ::= word (" " word)*', r'word ::= [^\x5B\x3C\x00-\x20]+',
        'cite ::= '+' | '.join(json.dumps('['+i+']') for i in ids),
        r'pad ::= ("\n" | "\n\n")?', r'sep ::= "\n" | "\n\n"'])+'\n'
save(RUN/'inputs.json',dict(status='DECODER_PROTOTYPE_NOT_PRODUCT_PROMOTION',started_utc=datetime.now(timezone.utc).isoformat(),sha256=hashes,
    baseline_profile=baseline,candidate_profile=candidate,candidate_system=prompt.SYSTEM,trigger_pattern=trigger,grammar_example=grammar(['S1','S2']),
    scope='Only final-output formatting constrained after completed think token. Reasoning unchanged. Known selected IDs only; no invented/added posthoc citations, validator unchanged. Grammar does not prove semantic entailment.'))
encoder=GraniteEncoder(ROOT/'models/v1.3/granite');prep=ROOT/'artifacts/v1.3/m4/repair-skills-prepared-0001';results=[]
with VerifiedPack(prep/'repair-skills.kpack',[(prep/'public-key.raw').read_bytes()],developer_mode=True) as pack,owned_server(RUN) as generator:
    registry=SessionRegistry();registry.activate(pack)
    generator.metadata['decoding_contract']='selected-citation-lines-lazy-after-think-v1-experimental'
    original_request=generator.request;original_generate=generator.generate;diagnostic={};current_grammar=''
    def request(endpoint,body=None):
        if endpoint=='/completion':
            body=dict(body,grammar=current_grammar,grammar_lazy=True,grammar_triggers=[dict(type=0,value=trigger,token=generator.tokenize(trigger,add_special=False)[0])])
        return original_request(endpoint,body)
    def generate(prepared):
        global current_grammar
        current_grammar=grammar(['S'+str(i+1) for i in range(len(prepared.evidence))])
        generated=original_generate(prepared);diagnostic.clear()
        diagnostic.update(grammar=current_grammar,grammar_sha256=hashlib.sha256(current_grammar.encode()).hexdigest())
        if generated.buffer.count('</think>')==1:
            final=generated.buffer.split('</think>',1)[1].strip()
            if '<think>' not in final and '<|' not in final:diagnostic['final_only']=final
        return generated
    generator.request=request;generator.generate=generate;runtime=PackRAG(registry,encoder,generator)
    for case in json.loads(gold.read_text())['cases']:
        if case['id'] not in ('FAN_CONNECTOR',):continue
        result=runtime.answer(Query(case['question'],case['as_of']))
        row=dict(id=case['id'],expected_state=case['expected_state'],result=result,diagnostic=diagnostic.copy(),scope='DECODING_PILOT_NOT_PRODUCT_PROMOTION')
        save(RUN/(case['id']+'.json'),row);results.append(row)
        print(case['id'],result['state'],result.get('rejection_reason'),result.get('timings',{}).get('generation',{}).get('emitted_token_count'),flush=True)
    gold_path=ROOT/'gates/g0/g0_v1.jsonl'
    save(RUN/'g0-inputs.json',dict(sha256=file_sha(gold_path),scope='Frozen direct gold-evidence generator gate, not retrieval/pack calibration'))
    for case in [json.loads(line) for line in gold_path.read_text().splitlines()]:
        if case['case_id'] not in ('G0-C02',):continue
        sources=case['evidence'];ids=[row['id'] for row in sources]
        assert ids==['S'+str(i+1) for i in range(len(ids))]
        text='\n\n'.join('<SOURCE id="'+row['id']+'">\n'+prompt.xml_escape(row['text'])+'\n</SOURCE>' for row in sources)
        user='<QUESTION>\n'+prompt.xml_escape(case['question'])+'\n</QUESTION>\n\n<CONTEXT>\nas_of_date=2026-10-12\nactive_packs=frozen-g0-evidence\n</CONTEXT>\n\n<VERIFIED_EVIDENCE>\n'+text+'\n</VERIFIED_EVIDENCE>'
        tokens=tuple(generator.render_tokens(prompt.SYSTEM,user));assert len(tokens)<=1536
        assert len(generator.tokenize(text,add_special=False))<=1200
        prepared=SimpleNamespace(tokens=tokens,max_new_tokens=min(1024,2048-len(tokens)),evidence=sources)
        generated=generator.generate(prepared);validated=validate_output(generated.buffer,set(ids),truncated=generated.truncated)
        final=validated.text or ''
        record=dict(id=case['case_id'],category=case['category'],question=case['question'],supplied_evidence=sources,
            state=validated.state,answer=validated.text,citations=list(validated.citations),rejection_reason=validated.reason,
            expected_facts=case['expected_facts'],required_citations=case['required_citations'],expected_abstention=case['expected_abstention'],
            missing_literal_facts=[v for v in case['expected_facts'] if v.casefold() not in final.casefold()],
            timings=generated.timings,prefill=len(tokens),max_new=prepared.max_new_tokens,generator=generator.metadata.copy(),
            diagnostic=diagnostic.copy(),manual_semantic_review_required=True)
        save(RUN/(case['case_id']+'.json'),record)
        print(case['case_id'],validated.state,validated.reason,generated.timings.get('emitted_token_count'),flush=True)
    assert file_sha(gold_path)==json.loads((RUN/'g0-inputs.json').read_text())['sha256']
for name,digest in hashes.items():assert file_sha(ROOT/name)==digest
save(RUN/'results.json',dict(status='COMPLETE_PROTOTYPE_MANUAL_ENTAILMENT_REVIEW_REQUIRED',cases=results,hidden_reasoning_saved=False))

