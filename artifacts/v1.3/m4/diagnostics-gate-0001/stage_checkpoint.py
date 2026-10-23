"""Exact E3 whitelist/index staging with existing accepted binary-safe Git reader."""
import hashlib,json
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
reader=ROOT/'artifacts/v1.3/m4/source-details-gate-0001/checkpoint_git.py'
spec=spec_from_file_location('e3_git_stage_reader',reader);module=module_from_spec(spec);spec.loader.exec_module(module)
git=module.git;blobs=module.blobs
def sha(data):return hashlib.sha256(data).hexdigest()
manifest=HERE/'checkpoint-files.json';record=json.loads(manifest.read_text());files=dict(record['files'])
files[manifest.relative_to(ROOT).as_posix()]=sha(manifest.read_bytes());files[Path(__file__).relative_to(ROOT).as_posix()]=sha(Path(__file__).read_bytes())
assert git('rev-parse','HEAD').stdout.decode().strip()==record['prior_e2_head']
assert not git('diff','--cached','--name-only').stdout.strip(),'Do not mix pre-existing staged work'
blocked={'.private','build','.gradle','.cxx','.kotlin','__pycache__','temp','stage','runner-temp','host-temp'}
forbidden={'.apk','.pyc','.class','.seed','.seed32','.pem','.key','.keystore','.jks','.gguf','.onnx','.safetensors'}
for n,v in files.items():
    p=ROOT/n;assert not blocked.intersection(part.lower() for part in Path(n).parts) and p.suffix.lower() not in forbidden,n
    assert p.resolve().is_relative_to(ROOT) and sha(p.read_bytes())==v,n
baseline=blobs('HEAD',sorted(files));changed={n for n,v in files.items() if baseline[n] is None or sha(baseline[n])!=v}
pathspec=HERE/'checkpoint-pathspec.utf8.nul';assert not pathspec.exists()
try:
    pathspec.write_bytes(b''.join(n.encode('utf-8')+b'\0' for n in sorted(files)))
    git('--literal-pathspecs','add','--pathspec-from-file='+str(pathspec),'--pathspec-file-nul')
finally:pathspec.unlink()
staged=set(git('diff','--cached','--name-only','-z').stdout.decode().split('\0'))-{''};assert staged==changed
index=blobs('',sorted(files))
for n,v in files.items():assert index[n] is not None and sha(index[n])==v,('Index bytes differ',n)
assert git('branch','--show-current').stdout.decode().strip()=='codex/packrag-v1.3'
print(json.dumps(dict(status='PASS_EXACT_E3_WHITELIST_STAGED',whitelisted=len(files),changed=len(staged))))
