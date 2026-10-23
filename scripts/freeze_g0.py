"""Extract the user-supplied 25 cases verbatim; never synthesize gate inputs."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSION = ROOT / 'docs/week1_mission.txt'

def main():
    text = MISSION.read_text(encoding='utf-8')
    parts = re.split(r'^## (G0-[DCAX]\d{2})\s*$', text, flags=re.M)
    cases = []
    categories = dict(D='direct', C='citation', A='abstention', X='adversarial')
    for i in range(1, len(parts), 2):
        case_id, body = parts[i:i+2]
        ev = re.search(r'Evidence:\s*```text\n(.*?)\n```', body, re.S).group(1)
        q = re.search(r'Question:\s*```text\n(.*?)\n```', body, re.S).group(1)
        evidences = re.split(r'^\[(S\d+)\]\s*\n', ev, flags=re.M)
        sources = [{'id': evidences[j], 'text': evidences[j+1].strip()} for j in range(1, len(evidences), 2)]
        expected = re.search(r'Expected(?: facts)?:\s*```text\n(.*?)\n```', body, re.S)
        abstain = case_id[3] == 'A'
        expected_text = expected.group(1) if expected else 'INSUFFICIENT_EVIDENCE'
        facts = [re.sub(r'\s*\[S\d+\]', '', s).strip() for s in expected_text.splitlines()]
        facts = [s for s in facts if s and s != 'INSUFFICIENT_EVIDENCE']
        cases.append(dict(case_id=case_id, category=categories[case_id[3]], question=q,
                          evidence=sources, expected_facts=facts,
                          required_citations=list(dict.fromkeys(re.findall(r'\[(S\d+)\]', expected_text))),
                          expected_abstention=abstain, adversarial=case_id[3]=='X'))
    assert len(cases) == 25
    out = ROOT / 'gates/g0'
    out.mkdir(parents=True, exist_ok=True)
    dataset = ''.join(json.dumps(c, ensure_ascii=False, separators=(',', ':'))+'\n' for c in cases).encode('utf-8')
    path = out / 'g0_v1.jsonl'
    if path.exists() and path.read_bytes() != dataset:
        raise RuntimeError('Frozen dataset already exists with different content')
    path.write_bytes(dataset)
    contract = re.search(r'# 10\. FROZEN G0 PROMPT CONTRACT.*?```text\n(.*?)\n```', text, re.S).group(1)
    (out / 'prompt_template.txt').write_bytes(contract.encode('utf-8'))
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [path, out/'prompt_template.txt']}
    hashes['mission_sha256'] = hashlib.sha256(MISSION.read_bytes()).hexdigest()
    (out/'freeze.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(hashes,indent=2))

if __name__ == '__main__': main()
