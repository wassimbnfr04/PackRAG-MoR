"""Download official, revision-pinned files into project-local storage."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(); p.add_argument('track',choices=['mor','granite','smollm2']); args=p.parse_args()
    if args.track=='mor':
        import gdown
        folder='https://drive.google.com/drive/folders/1pYKJOu2aBGC-jgoWbfP6T_vqEYtUVxa4'
        entries=gdown.download_folder(folder,skip_download=True,remaining_ok=True)
        if not entries: raise RuntimeError('Official Drive folder unavailable')
        (ROOT/'artifacts/week1/environment/mor_drive_listing.json').write_text(json.dumps([str(e) for e in entries],indent=2),encoding='utf-8')
        print(entries,flush=True)
        # Match the authors' published rec3 expert-choice release, never substitute another model.
        experiment='250720_pretrain_smollm-360m_rec3_middle_cycle_random_lr3e-3_mor_expert_linear_alpha_0.1_sigmoid_aux_loss_0.001'
        selected=[e for e in entries if Path(e.path).parts[0]==experiment and Path(e.path).name!='training_args.bin']
        if not selected: raise RuntimeError('Official 360M rec3 expert-choice checkpoint not identified')
        for e in selected:
            target=ROOT/'reference/mor/checkpoints'/experiment/Path(e.path).name
            target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():
                result=gdown.download(id=e.id,output=str(target),quiet=False)
                if not result: raise RuntimeError('Official checkpoint download failed')
    else:
        from huggingface_hub import snapshot_download
        metadata=json.loads((ROOT/f'artifacts/week1/environment/{args.track}_model_metadata.json').read_text())
        revision=metadata['sha']; model=metadata['id']
        target=ROOT/'models'/args.track
        snapshot_download(model,revision=revision,local_dir=target,
                          allow_patterns=['*.json','model.safetensors','*.txt'],
                          cache_dir=ROOT/'.cache/huggingface')
        print(model,revision,flush=True)
    directory=ROOT/'reference/mor/checkpoints' if args.track=='mor' else ROOT/'models'/args.track
    hashes={str(f.relative_to(directory)):hashlib.sha256(f.read_bytes()).hexdigest() for f in directory.rglob('*') if f.is_file() and '.cache' not in f.parts}
    (ROOT/f'artifacts/week1/environment/{args.track}_artifact_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print(json.dumps(hashes,indent=2),flush=True)

if __name__=='__main__': main()
