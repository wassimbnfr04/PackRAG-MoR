import hashlib
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from reference.mor.backend import PyTorchMoRBackend

def prompt_for(case):
    template=(Path(__file__).parent/'prompt_template.txt').read_text(encoding='utf-8')
    evidence='\n\n'.join('['+e['id']+']\n'+e['text'] for e in case['evidence'])
    return template.replace('{question}',case['question']).replace('{evidence}',evidence)

def main():
    directory=Path(__file__).parent;freeze=json.loads((directory/'freeze.json').read_text())
    for name in ('g0_v1.jsonl','prompt_template.txt'):
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest()==freeze[name],'Frozen input changed'
    result=directory/'g0_results.jsonl'
    if result.exists():raise RuntimeError('Primary outputs exist. Do not overwrite or rerun primary G0.')
    if json.loads((ROOT/'export/golden_mor_reference.json').read_text())['status']!='PASS':raise RuntimeError('Reference preflight not passed')
    cases=[json.loads(s) for s in (directory/'g0_v1.jsonl').read_text(encoding='utf-8').splitlines()]
    backend=PyTorchMoRBackend(); info=backend.load()
    with result.open('x',encoding='utf-8',newline='\n') as out:
        for case in cases:
            prompt=prompt_for(case)
            record=dict(case_id=case['case_id'],category=case['category'],prompt=prompt,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                        decoding=dict(temperature=0,greedy=True,top_p=1.0,batch_size=1,max_new_tokens=128),model=info,
                        **asdict(backend.generate(prompt)))
            out.write(json.dumps(record,ensure_ascii=False)+'\n');out.flush();os.fsync(out.fileno())
            print(case['case_id'],'saved',flush=True)
    (directory/'primary_results.sha256').write_text(hashlib.sha256(result.read_bytes()).hexdigest()+'\n',encoding='ascii')
    print('Primary G0 saved and hashed. No diagnostic prompt changes were made.',flush=True)

if __name__=='__main__':main()
