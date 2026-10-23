"""Zero-row KDX/SQLite contract is valid; freeze a signed empty developer pack."""
import argparse
import hashlib
import json
import shutil
import sqlite3
import struct
import zipfile
from pathlib import Path
from nacl.signing import SigningKey
from kpack_builder.core import canonical, key_id, sha
from product.packrag.config import file_sha
from scripts.v13_archive_fixtures import archive

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--run",type=Path,required=True); args=parser.parse_args()
    run=args.run.resolve(); assert run.is_relative_to(ROOT); run.mkdir(parents=True,exist_ok=False)
    asset=ROOT/"product/android/app/src/androidTest/assets/empty-corpus"; assert not asset.exists()
    source=ROOT/"artifacts/v1.3/m1/smoke-0001/developer-pack/walking-skeleton.kpack"
    with zipfile.ZipFile(source) as z: payloads={name:z.read(name) for name in z.namelist()}
    manifest=json.loads(payloads.pop("manifest.json")); payloads.pop("manifest.sig")
    work=run/"empty.sqlite"; work.write_bytes(payloads["knowledge.sqlite"])
    db=sqlite3.connect(work)
    try:
        with db:
            for table in ("aliases","relations","derived_texts","chunks","sources"): db.execute("DELETE FROM "+table)
            db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
    finally: db.close()
    payloads["knowledge.sqlite"]=work.read_bytes(); assert work.parent==run; work.unlink()
    header=bytearray(payloads["dense.kdx"][:84]); struct.pack_into("<I",header,16,0); header[52:84]=hashlib.sha256(canonical([])).digest(); payloads["dense.kdx"]=bytes(header)
    signer=SigningKey.generate(); public=bytes(signer.verify_key); (run/"public-key.raw").write_bytes(public)
    manifest["pack_id"]="org.packrag.development.empty"; manifest["version"]="1.0.0"; manifest["publisher"]["key_id"]=key_id(public); manifest["counts"]={"sources":0,"chunks":0,"relations":0}
    manifest["files"]=[dict(path=p,sha256=sha(b),bytes=len(b),media_type="application/vnd.sqlite3" if p.endswith(".sqlite") else "application/octet-stream",required=True) for p,b in sorted(payloads.items())]
    raw=canonical(manifest); output=run/"empty.kpack"; output.write_bytes(archive(sorted({**payloads,"manifest.json":raw,"manifest.sig":signer.sign(raw).signature}.items())))
    record=dict(purpose="SYNTHETIC_VALID_ZERO_ROW_FORMAT_BOUNDARY",filename=output.name,sha256=file_sha(output),manifest_sha256=sha(raw),public_key_sha256=file_sha(run/"public-key.raw"),source_pack_sha256=file_sha(source),private_seed="EPHEMERAL_NOT_SAVED",script_sha256=file_sha(Path(__file__)))
    (run/"case.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8"); asset.mkdir()
    for path in run.iterdir(): shutil.copyfile(path,asset/path.name)
    print("Frozen valid empty KPack")

if __name__=="__main__": main()
