"""Create/resume one locally held project publisher; publish only public metadata."""
import argparse
import json
import os
from datetime import datetime,timezone
from pathlib import Path
from nacl.signing import SigningKey
from kpack_builder.core import key_id
from product.packrag.config import file_sha
from product.packrag.trust import trusted_publishers

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--run",type=Path,required=True); args=parser.parse_args()
    run=args.run.resolve(); assert run.is_relative_to(ROOT); run.mkdir(parents=True,exist_ok=False)
    custody=ROOT/"product/.private"; assert custody.is_dir(),"Prepare owner-only private directory permissions first"
    seed=custody/"demo-publisher.seed"
    existed=seed.exists()
    if existed:
        data=seed.read_bytes(); assert len(data)==32; signer=SigningKey(data)
    else:
        signer=SigningKey.generate()
        descriptor=os.open(seed,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(descriptor,"wb") as stream: stream.write(bytes(signer)); stream.flush(); os.fsync(stream.fileno())
    public=bytes(signer.verify_key)
    metadata=dict(schema_version="1.0",approval_scope="packrag-project-demonstrators",publishers=[dict(name="PackRAG project demonstrator publisher",key_id=key_id(public),public_key_hex=public.hex())])
    assert trusted_publishers(metadata)==(public,)
    raw=(json.dumps(metadata,sort_keys=True,indent=2)+"\n").encode()
    targets=[ROOT/"product/config/release-trust.json",ROOT/"product/android/app/src/main/assets/release-trust.json"]
    for target in targets:
        if target.exists(): assert target.read_bytes()==raw,"Existing approved configuration differs; no silent key rotation"
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open("xb") as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    record=dict(status="PUBLIC_CONFIGURATION_CREATED_NOT_RELEASE_ACCEPTANCE",recorded_utc=datetime.now(timezone.utc).isoformat(),publisher=metadata["publishers"][0],private_seed_reused=existed,
        private_seed="LOCAL_OWNER_ONLY_NOT_EXPORTED",public_configuration_sha256={p.relative_to(ROOT).as_posix():file_sha(p) for p in targets},script_sha256=file_sha(Path(__file__)),
        limits="Project-owned demonstrator signer; not original source authority, source truth, calibration quality or final release approval. Private seed is excluded from tracked/delivery artifacts.")
    (run/"publisher-setup.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print(record["status"],metadata["publishers"][0]["key_id"])

if __name__=="__main__": main()
