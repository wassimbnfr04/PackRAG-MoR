"""Explicit benchmark diagnostics: final-only rejected text, never hidden reasoning.

Same frozen documents/questions/runtime. No prompt, policy, token, model or
admission changes. Diagnostic text is NOT accepted product output.
"""
import json, re, sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from product.packrag.config import file_sha
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack,SessionRegistry
from product.packrag.runtime import PackRAG
from product.packrag.retrieval import Query
from scripts.v13_smoke import owned_server,save
HERE=Path(__file__).resolve().parent
RUN=ROOT/'artifacts/v1.3/m4/repair-diagnostics-desktop-0002'
RUN.mkdir(exist_ok=False)
inputs=[Path(__file__),HERE/'repair-cases-frozen-0001.json',HERE/'repair-documents-frozen-0001.json']
hashes={str(p.relative_to(ROOT)):file_sha(p) for p in inputs}
save(RUN/'inputs.json',dict(sha256=hashes,started_utc=datetime.now(timezone.utc).isoformat(),scope='FINAL_ONLY_DEVELOPER_DIAGNOSTIC_NOT_PRODUCT_ANSWER'))
prep=ROOT/'artifacts/v1.3/m4/repair-skills-prepared-0001'
encoder=GraniteEncoder(ROOT/'models/v1.3/granite')
cases=json.loads(inputs[1].read_text())['cases']
with VerifiedPack(prep/'repair-skills.kpack',[(prep/'public-key.raw').read_bytes()],developer_mode=True) as pack,owned_server(RUN) as generator:
    registry=SessionRegistry();registry.activate(pack)
    original_request=generator.request
    completion={}
    def request(endpoint,body=None):
        result=original_request(endpoint,body)
        if endpoint=='/completion':
            completion.clear()
            for name in ('stop_type','stopped_limit','stopped_eos','stopped_word','stopping_word','truncated','tokens_predicted'):
                if name in result:completion[name]=result[name]
        return result
    generator.request=request
    original_generate=generator.generate
    diagnostic={}
    def generate(prompt):
        value=original_generate(prompt)
        diagnostic.clear();diagnostic.update(completion)
        if value.buffer.count('</think>')==1:
            final=value.buffer.split('</think>',1)[1].strip()
            if '<think>' not in final and '<|' not in final:
                diagnostic.update(final_only=final,paragraphs=[dict(characters=len(p),cited=bool(re.search(r'\[S[1-9]\d*\]',p)),heading_marker=p.startswith('#'),list_marker=bool(re.match(r'(?:\d+[.)]|[-*]) ',p))) for p in re.split(r'\n\s*\n',final)])
        return value
    generator.generate=generate
    runtime=PackRAG(registry,encoder,generator)
    for case in cases:
        if case['id'] not in ('FAN_FULL_GUIDE','FAN_SAFE_START','FAN_CONNECTOR'):continue
        result=runtime.answer(Query(case['question'],case['as_of']))
        save(RUN/(case['id']+'.json'),dict(id=case['id'],result=result,diagnostic=diagnostic.copy(),scope='REJECTED_FINAL_IS_DIAGNOSTIC_NOT_PRODUCT_OUTPUT',hidden_reasoning_saved=False))
        print(case['id'],result['state'],result.get('rejection_reason'),completion,flush=True)
for name,digest in hashes.items():assert file_sha(ROOT/name)==digest
save(RUN/'complete.json',dict(status='COMPLETE_DIAGNOSTICS_NOT_SKILL_ACCEPTANCE',sha256=hashes,hidden_reasoning_saved=False))

