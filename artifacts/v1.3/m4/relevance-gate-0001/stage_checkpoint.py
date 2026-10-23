"""Stage only this verified checkpoint, asserting exact expected changed subset and index bytes."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
def git(*args,check=True):
 return subprocess.run(['git','-c','safe.directory='+ROOT.as_posix(),'-c','core.autocrlf=false',*args],cwd=ROOT,capture_output=True,check=check)
def sha(data):return hashlib.sha256(data).hexdigest()
manifest=HERE/'checkpoint-files.json'
record=json.loads(manifest.read_text());files=dict(record['files'])
files[manifest.relative_to(ROOT).as_posix()]=sha(manifest.read_bytes())
assert not git('diff','--cached','--name-only').stdout.strip(),'Existing staged work must not be mixed'
expected_changed=set()
for name,expected in files.items():
 assert sha((ROOT/name).read_bytes())==expected,name
 old=git('show','HEAD:'+name,check=False)
 if old.returncode or sha(old.stdout)!=expected:expected_changed.add(name)
# Structured argument list, no shell expansion or broad directory staging.
git('add','--',*sorted(files))
staged=set(git('diff','--cached','--name-only','-z').stdout.decode().split('\0'))-{''}
assert staged==expected_changed,(sorted(staged-expected_changed),sorted(expected_changed-staged))
for name,expected in files.items():
 assert sha(git('show',':'+name).stdout)==expected,('Index bytes differ',name)
assert git('branch','--show-current').stdout.decode().strip()=='codex/packrag-v1.3'
print(json.dumps(dict(status='PASS_EXACT_CHECKPOINT_STAGED',whitelisted=len(files),changed=len(staged))))
