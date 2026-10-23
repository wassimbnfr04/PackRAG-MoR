"""Prepare the existing guarded stage workflow; this performs no Git mutation."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent;prior=HERE.parent/'representation-gate-0002/stage_checkpoint.py'
raw=prior.read_bytes();text=raw.decode();assert text.count('D2')==2
prepared=text.replace('D2','D3');target=HERE/'stage_checkpoint.py';assert not target.exists();target.write_text(prepared)
record=HERE/'checkpoint-stage-derivation.json';assert not record.exists()
record.write_text(json.dumps(dict(status='PREPARED_NOT_STAGED_OR_COMMITTED',base=prior.name,
    base_sha256=hashlib.sha256(raw).hexdigest(),target_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    literal_change=dict(before='D2',after='D3',count=2)),indent=2)+'\n')
print('CHECKPOINT_STAGE_PREPARED_NO_GIT_MUTATION')
