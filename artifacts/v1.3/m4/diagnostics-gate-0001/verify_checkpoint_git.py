"""After actual commit: verify exact checkpoint bytes without changing Git/files."""
import hashlib,json
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
reader=ROOT/'artifacts/v1.3/m4/source-details-gate-0001/checkpoint_git.py'
spec=spec_from_file_location('e3_committed_git_reader',reader);module=module_from_spec(spec);spec.loader.exec_module(module)
record=json.loads((HERE/'checkpoint-files.json').read_text());files=dict(record['files'])
files[(HERE/'checkpoint-files.json').relative_to(ROOT).as_posix()]=hashlib.sha256((HERE/'checkpoint-files.json').read_bytes()).hexdigest()
files[(HERE/'stage_checkpoint.py').relative_to(ROOT).as_posix()]=hashlib.sha256((HERE/'stage_checkpoint.py').read_bytes()).hexdigest()
head=module.git('rev-parse','HEAD').stdout.decode().strip();assert head!=record['prior_e2_head']
assert module.git('rev-parse','HEAD^').stdout.decode().strip()==record['prior_e2_head']
blobs=module.blobs('HEAD',sorted(files))
for n,v in files.items():assert blobs[n] is not None and hashlib.sha256(blobs[n]).hexdigest()==v,n
assert not module.git('diff','--cached','--name-only').stdout.strip()
print(json.dumps(dict(status='PASS_EXACT_E3_COMMITTED_CHECKPOINT_BYTES',head=head,whitelist_files=len(files))))
