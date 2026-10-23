"""Correct literal newline spelling from the recorded inline document append."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;p=ROOT/'docs/v1.3/M4E3_METHODS.md'
b=p.read_bytes();t=b.decode('utf-8');prefix='\\n19:45 UTC';assert t.count(prefix)==1
start=t.index(prefix);end=t.index('\\n',start+2)+2;fragment=t[start:end];assert 'Desktop0015' in fragment
saved=HERE/'M4E3_METHODS-before-literal-newline-repair.md';assert not saved.exists();saved.write_bytes(b)
p.write_text(t[:start]+fragment.replace('\\n','\n')+t[end:],encoding='utf-8')
target=HERE/'methods-newline-repair.json';assert not target.exists();target.write_text(json.dumps(dict(status='DOCUMENT_FORMAT_CORRECTION_ONLY',
    before_sha256=hashlib.sha256(b).hexdigest(),after_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
    scope='Replace exactly two literal newline escapes in the19:45 document append with actual newlines; content and all runtime/results unchanged.'),indent=2)+'\n',encoding='utf-8')
print('PASS exact document formatting repair')
