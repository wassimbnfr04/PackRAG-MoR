"""Exact E1 checkpoint staging; NUL pathspec avoids Windows argv-size limits."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
def git(*args,check=True):return subprocess.run(['git','-c','safe.directory='+ROOT.as_posix(),'-c','core.autocrlf=false',*args],cwd=ROOT,capture_output=True,check=check)
def sha(data):return hashlib.sha256(data).hexdigest()
manifest=HERE/'checkpoint-files.json';record=json.loads(manifest.read_text());files=dict(record['files'])
files[manifest.relative_to(ROOT).as_posix()]=sha(manifest.read_bytes())
# Operational helper is additional to the verified runtime/evidence whitelist;
# its own bytes are checked explicitly, never labeled tested runtime source.
files[Path(__file__).relative_to(ROOT).as_posix()]=sha(Path(__file__).read_bytes())
assert not git('diff','--cached','--name-only').stdout.strip(),'Do not mix existing staged work'
expected_changed=set()
for name,expected in files.items():
    path=ROOT/name;assert path.resolve().is_relative_to(ROOT) and '.private' not in path.parts and sha(path.read_bytes())==expected,name
    old=git('show','HEAD:'+name,check=False)
    if old.returncode or sha(old.stdout)!=expected:expected_changed.add(name)
pathspec=HERE/'checkpoint-pathspec.utf8.nul';assert not pathspec.exists()
try:
    pathspec.write_bytes(b''.join(name.encode('utf-8')+b'\0' for name in sorted(files)))
    git('--literal-pathspecs','add','--pathspec-from-file='+str(pathspec),'--pathspec-file-nul')
finally:pathspec.unlink()
staged=set(git('diff','--cached','--name-only','-z').stdout.decode().split('\0'))-{''}
assert staged==expected_changed,(sorted(staged-expected_changed),sorted(expected_changed-staged))
for name,expected in files.items():assert sha(git('show',':'+name).stdout)==expected,('Index bytes differ',name)
assert git('branch','--show-current').stdout.decode().strip()=='codex/packrag-v1.3'
print(json.dumps(dict(status='PASS_EXACT_E1_CHECKPOINT_STAGED',whitelisted=len(files),changed=len(staged),operational_helper_additional=True)))
