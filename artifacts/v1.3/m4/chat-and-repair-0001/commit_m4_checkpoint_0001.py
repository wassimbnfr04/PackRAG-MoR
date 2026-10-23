"""Exact raw public checkpoint; never reset/stage unrelated legacy changes."""
import hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path.cwd();GATE=ROOT/'artifacts/v1.3/m4/chat-repair-final-gate-0001'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
git=['git','-c','safe.directory='+ROOT.as_posix()]
def command(*args,**kwargs):return subprocess.run([*git,*args],cwd=ROOT,capture_output=True,check=True,**kwargs)
assert command('diff','--cached','--name-only').stdout.strip()==b'', 'Existing staged changes must not be mixed'
original=json.loads((GATE/'checkpoint-whitelist.json').read_text())
rows=original['files']
for n,row in rows.items():
 # Only durable Markdown evolved after preparation; all source/result bytes stay exact.
 actual=sha(ROOT/n)
 if actual!=row['sha256']:
  assert Path(n).suffix=='.md' and (n in ['PLAN.md','STATUS.md','DECISIONS.md','product/README.md'] or n.startswith('docs/')),n
  row['sha256']=actual;row['bytes']=(ROOT/n).stat().st_size
for p in [GATE/'checkpoint-whitelist.json',Path(__file__).resolve()]:rows[p.relative_to(ROOT).as_posix()]=dict(sha256=sha(p),bytes=p.stat().st_size)
manifest=GATE/'checkpoint-whitelist-0002.json';assert not manifest.exists()
manifest.write_text(json.dumps(dict(status='FINAL_EXACT_PUBLIC_WHITELIST_BEFORE_COMMIT',files=rows,count=len(rows),bytes=sum(v['bytes'] for v in rows.values()),scope=original['scope']),indent=2)+'\n',encoding='utf-8')
rows[manifest.relative_to(ROOT).as_posix()]=dict(sha256=sha(manifest),bytes=manifest.stat().st_size)
names=sorted(rows);assert all('\n' not in n and '\t' not in n and '"' not in n for n in names)
for n in names:assert sha(ROOT/n)==rows[n]['sha256'],n
parent=command('rev-parse','HEAD').stdout.decode().strip()
# --no-filters binds exact working bytes, including profile/signature/fixture newline identities.
oids=command('hash-object','-w','--no-filters','--stdin-paths',input=('\n'.join(names)+'\n').encode()).stdout.decode().splitlines();assert len(oids)==len(names)
index=''.join(f'100644 {oid}\t{name}\n' for name,oid in zip(names,oids))
command('update-index','--add','--index-info',input=index.encode('utf-8'))
def verify_blobs(prefix):
 output=command('cat-file','--batch',input=''.join(prefix+n+'\n' for n in names).encode('utf-8')).stdout
 offset=0
 for name in names:
  end=output.index(b'\n',offset);header=output[offset:end].split();assert len(header)==3 and header[1]==b'blob',name
  size=int(header[2]);offset=end+1;blob=output[offset:offset+size];offset+=size
  assert output[offset:offset+1]==b'\n';offset+=1
  assert hashlib.sha256(blob).hexdigest()==rows[name]['sha256'],name
 assert offset==len(output)
verify_blobs(':')
changed=command('diff','--cached','--name-only','-z').stdout.decode().split('\0');changed=[n for n in changed if n]
assert changed and set(changed)<=set(names)
result=command('commit','-m','Complete M4 chat and validated quoted repair runtime')
head=command('rev-parse','HEAD').stdout.decode().strip()
assert command('rev-parse','HEAD^').stdout.decode().strip()==parent
assert command('diff','--cached','--name-only').stdout.strip()==b''
assert set(command('diff-tree','--no-commit-id','--name-only','-r','HEAD','-z').stdout.decode().strip('\0').split('\0'))==set(changed)
verify_blobs('HEAD:')
proof=GATE/'checkpoint-verification-0001.json';assert not proof.exists()
proof.write_text(json.dumps(dict(status='PASS_EXACT_PUBLIC_M4_CHECKPOINT',utc=datetime.now(timezone.utc).isoformat(),commit=head,parent=parent,whitelist_sha256=sha(manifest),declared_public_files=len(names),changed_files=len(changed),raw_staged_and_committed_blob_sha256_verified=True,committed_files=changed,commit_stdout=result.stdout.decode(errors='replace'),scope='Exact accepted public v1.3 checkpoint. No unrelated legacy changes, weights/exports/APKs/rawHTML/private custody reset or staged. Working durable state may evolve after this proof.'),indent=2)+'\n',encoding='utf-8')
print('PASS_EXACT_PUBLIC_M4_CHECKPOINT',head,len(changed),'changed files',flush=True)
