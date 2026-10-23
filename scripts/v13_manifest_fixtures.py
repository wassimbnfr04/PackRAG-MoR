"""New signed hostile-manifest corpus; test-only ephemeral key, never release calibration."""
import argparse
import json
import shutil
import zipfile
from pathlib import Path
from nacl.signing import SigningKey
from kpack_builder.core import canonical, key_id
from product.packrag.config import file_sha
from product.tests.test_manifest import mutate_manifest

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--run", type=Path, required=True); args = parser.parse_args()
    run = args.run.resolve(); assert run.is_relative_to(ROOT); run.mkdir(parents=True, exist_ok=False)
    asset = ROOT/"product/android/app/src/androidTest/assets/manifest-corpus"
    assert not asset.exists(), "Do not overwrite an existing frozen fixture corpus"
    corpus = json.loads((ROOT/"product/tests/manifest-cases.json").read_text())
    original = ROOT/"artifacts/v1.3/m1/smoke-0001/developer-pack/walking-skeleton.kpack"
    with zipfile.ZipFile(original) as archive: payloads = {name: archive.read(name) for name in archive.namelist()}
    base = json.loads(payloads.pop("manifest.json")); payloads.pop("manifest.sig")
    signer = SigningKey.generate(); public = bytes(signer.verify_key)
    base["publisher"]["key_id"] = key_id(public)
    (run/"public-key.raw").write_bytes(public)
    cases = []
    for case in corpus:
        manifest = mutate_manifest(base, case); raw = canonical(manifest)
        path = run/(case["id"]+".kpack")
        with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted({**payloads,"manifest.json":raw,"manifest.sig":signer.sign(raw).signature}.items()):
                info=zipfile.ZipInfo(name,(1980,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100600<<16
                archive.writestr(info,data)
        cases.append(dict(id=case["id"],filename=path.name,accept=case["accept"],developer_mode=case.get("developer_mode",True),sha256=file_sha(path)))
    (run/"cases.json").write_text(json.dumps(dict(cases=cases,public_key_sha256=file_sha(run/"public-key.raw"),
        purpose="SIGNED_MANIFEST_SCHEMA_NEGATIVES_NOT_RELEASE_CALIBRATION",private_seed="EPHEMERAL_NOT_SAVED",
        source_pack_sha256=file_sha(original),corpus_sha256=file_sha(ROOT/"product/tests/manifest-cases.json")),indent=2)+"\n",encoding="utf-8")
    asset.mkdir();
    for path in run.iterdir(): shutil.copyfile(path,asset/path.name)
    print("Frozen signed cases:",len(cases))

if __name__ == "__main__": main()
