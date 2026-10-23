"""Freeze authenticated versions for Android lifecycle/process-loss tests."""
import argparse
import copy
import json
import shutil
import zipfile
from pathlib import Path
from nacl.signing import SigningKey
from kpack_builder.core import canonical, key_id
from product.packrag.config import file_sha
from scripts.v13_archive_fixtures import archive

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--run",type=Path,required=True); args=parser.parse_args()
    run=args.run.resolve(); assert run.is_relative_to(ROOT); run.mkdir(parents=True,exist_ok=False)
    asset=ROOT/"product/android/app/src/androidTest/assets/lifecycle-corpus"; assert not asset.exists()
    source=ROOT/"artifacts/v1.3/m1/smoke-0001/developer-pack/walking-skeleton.kpack"
    with zipfile.ZipFile(source) as z: original={name:z.read(name) for name in z.namelist()}
    base=json.loads(original.pop("manifest.json")); original.pop("manifest.sig")
    signer=SigningKey.generate(); public=bytes(signer.verify_key); (run/"public-key.raw").write_bytes(public); records=[]
    for identifier,version,domain in [("v1","1.0.0","technical"),("v2","1.0.1","technical"),("v3","1.0.10","technical"),("older","0.9.0","technical"),("equal-build","1.0.1+build2","technical"),("collision","1.0.1","different-synthetic-domain")]:
        manifest=copy.deepcopy(base); manifest["publisher"]["key_id"]=key_id(public); manifest["version"]=version; manifest["domain"]=domain
        raw=canonical(manifest); data=archive(sorted({**original,"manifest.json":raw,"manifest.sig":signer.sign(raw).signature}.items()))
        output=run/(identifier+".kpack"); output.write_bytes(data)
        records.append(dict(id=identifier,filename=output.name,version=version,sha256=file_sha(output),manifest_sha256=__import__('hashlib').sha256(raw).hexdigest()))
    record=dict(purpose="SYNTHETIC_IMMUTABLE_VERSIONS_NOT_RELEASE_CALIBRATION",cases=records,public_key_sha256=file_sha(run/"public-key.raw"),source_pack_sha256=file_sha(source),private_seed="EPHEMERAL_NOT_SAVED",script_sha256=file_sha(Path(__file__)))
    (run/"cases.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8"); asset.mkdir()
    for path in run.iterdir(): shutil.copyfile(path,asset/path.name)
    print("Frozen lifecycle versions:",len(records))

if __name__=="__main__": main()
