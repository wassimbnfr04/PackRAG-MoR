import hashlib
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_primary_inputs_and_complete_outputs_are_frozen():
    directory=ROOT/'gates/g0'; freeze=json.loads((directory/'freeze.json').read_text())
    for name in ('g0_v1.jsonl','prompt_template.txt'):
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest()==freeze[name]
    cases=[json.loads(s) for s in (directory/'g0_v1.jsonl').read_text(encoding='utf-8').splitlines()]
    results=[json.loads(s) for s in (directory/'g0_results.jsonl').read_text(encoding='utf-8').splitlines()]
    assert Counter(c['category'] for c in cases)=={'direct':10,'citation':5,'abstention':5,'adversarial':5}
    assert [c['case_id'] for c in cases]==[r['case_id'] for r in results]
    assert hashlib.sha256((directory/'g0_results.jsonl').read_bytes()).hexdigest()==(directory/'primary_results.sha256').read_text().strip()
    assert all(r['decoding']==dict(temperature=0,greedy=True,top_p=1.0,batch_size=1,max_new_tokens=128) for r in results)
    assert all(r['generated_tokens']==len(r['generated_ids']) for r in results)
