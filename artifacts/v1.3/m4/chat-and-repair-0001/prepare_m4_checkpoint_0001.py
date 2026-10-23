"""Prepare exact public v1.3 source/evidence whitelist; do not stage unrelated legacy dirt."""
import hashlib,json
from pathlib import Path
from scripts.v13_result_manifest import public_path,public_tree_files
ROOT=Path.cwd();OUT=ROOT/'artifacts/v1.3/m4/chat-repair-final-gate-0001/checkpoint-whitelist.json'
assert not OUT.exists()
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
paths=set()
android=json.loads((ROOT/'artifacts/v1.3/m4/build-0122/source-at-build-start.json').read_text())['files']
for n,h in android.items():assert sha(ROOT/n)==h;paths.add(ROOT/n)
python=json.loads((ROOT/'artifacts/v1.3/m4/quote-complete-python-regression-0001/inputs.json').read_text())
for n,h in python.items():
 p=ROOT/n;assert sha(p)==h
 rel=p.relative_to(ROOT).as_posix()
 if rel.startswith('product/') or rel.startswith('scripts/v13_'):paths.add(p)
for top in ['docs/v1.3','docs/adr']:
 paths.update(public_tree_files(ROOT,top))
paths.update(ROOT/n for n in ['PLAN.md','STATUS.md','DECISIONS.md','product/README.md'])
tops=[]
prefixes=('repair-','product-quote','quote-','chat-walking','emulator-chat','phone-chat','phone-native-quote','phone-quoted','emulator-native-quote')
for directory in (ROOT/'artifacts/v1.3/m4').iterdir():
 if directory.is_dir() and not directory.name.endswith('-temp') and (
  directory.name.startswith(prefixes) or directory.name in ['chat-and-repair-0001','chat-repair-final-gate-0001','consolidated-f3-f4-0001'] or directory.name in {f'build-{n:04}' for n in range(106,123)}):tops.append(directory.relative_to(ROOT).as_posix())
blocked={'.apk','.gguf','.onnx','.pt','.pth','.safetensors','.zip','.7z','.exe','.dll','.so','.o','.pdb','.html','.seed','.pem','.p12','.keystore'}
omitted=[]
for top in tops:
 for p in public_tree_files(ROOT,top):
  if p.suffix.lower() in blocked or p.stat().st_size>32_000_000 or 'private-key' in p.name.lower() or 'private_seed' in p.name.lower():
   omitted.append(p.relative_to(ROOT).as_posix());continue
  paths.add(p)
rows={}
for p in sorted(paths):
 assert public_path(ROOT,p) and p.is_file()
 assert p.suffix.lower() not in blocked and 'private-key' not in p.name.lower() and 'private_seed' not in p.name.lower(),p
 rows[p.relative_to(ROOT).as_posix()]=dict(sha256=sha(p),bytes=p.stat().st_size)
OUT.write_text(json.dumps(dict(status='PREPARED_EXACT_PUBLIC_V13_WHITELIST_NOT_COMMIT',files=rows,count=len(rows),bytes=sum(v['bytes'] for v in rows.values()),omitted_large_or_nonredistributable=omitted,scope='Accepted v1.3 source/docs/evidence only; no weights/exports/APKs/private custody/rawHTML/generated caches or unrelated legacy changes. Raw staged blobs must match every declared hash before commit.'),indent=2)+'\n',encoding='utf-8')
print('PREPARED',len(rows),'public files',sum(v['bytes'] for v in rows.values()),'bytes',flush=True)
