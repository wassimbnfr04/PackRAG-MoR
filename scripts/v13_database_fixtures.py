"""Sign deliberately invalid DBs with matching payload hashes; no private key persisted."""
import argparse
import copy
import json
import shutil
import sqlite3
import zipfile
from contextlib import closing
from pathlib import Path
from nacl.signing import SigningKey
from kpack_builder.core import canonical, key_id, sha
from product.packrag.config import file_sha

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--run",type=Path,required=True); args=parser.parse_args()
    run=args.run.resolve(); assert run.is_relative_to(ROOT); run.mkdir(parents=True,exist_ok=False)
    asset=ROOT/"product/android/app/src/androidTest/assets/database-corpus"; assert not asset.exists()
    source=ROOT/"artifacts/v1.3/m1/smoke-0001/developer-pack/walking-skeleton.kpack"
    with zipfile.ZipFile(source) as z: original={name:z.read(name) for name in z.namelist()}
    base=json.loads(original.pop("manifest.json")); original.pop("manifest.sig")
    signer=SigningKey.generate(); public=bytes(signer.verify_key); (run/"public-key.raw").write_bytes(public)
    cases=json.loads((ROOT/"product/tests/database-cases.json").read_text()); records=[]
    for case in cases:
        manifest=copy.deepcopy(base); manifest["publisher"]["key_id"]=key_id(public); manifest.update(case.get("manifest",{}))
        if case.get("calibrated"):
            manifest["calibration"]=dict(method="candidate-relevance-v1.3",dataset_sha256="a"*64,min_agreed_dense_cosine=0.5,min_dense_only_cosine=0.8,precision=0.9,recall=0.8)
        payloads=original.copy(); work=run/(case["id"]+".sqlite"); work.write_bytes(payloads["knowledge.sqlite"])
        with closing(sqlite3.connect(work)) as db,db:
            ids=[r[0] for r in db.execute("SELECT chunk_id FROM chunks ORDER BY dense_row")]
            if case.get("snapshot"):
                text,source_id=db.execute("SELECT canonical_text,source_id FROM chunks WHERE dense_row=0").fetchone()
                payloads["sources/original.txt"]=text.encode("utf-8")
                db.execute("UPDATE sources SET snapshot_path='sources/original.txt',sha256_original=? WHERE source_id=?",(sha(payloads["sources/original.txt"]),source_id))
            if (r:=case.get("relation")):
                db.execute("INSERT INTO relations VALUES(?,?,?,?,?)",(ids[0],r.get("target",ids[1]),r["type"],r["provenance"],r["confidence"]))
            if (d:=case.get("derived")):
                text="Synthetic derived-text contract fixture only."
                db.execute("INSERT INTO derived_texts VALUES(?,?,?,?,?,?,?,?,?)",(d.get("chunk_id",ids[0]),"generator",d.get("language","en"),text,d.get("hash",sha(text.encode())),d["method"],d.get("source","SYNTHETIC_TEST_PROVENANCE_NOT_OFFICIAL_REVIEW"),d.get("reviewer","SYNTHETIC_TEST_REVIEWER_NOT_A_PERSON"),d.get("reviewed_at","2026-10-05")))
            for sql in case.get("sql",[]): db.execute(sql)
            # Keep FTS consistent after ordinary mutations; dedicated failure cases deliberately break it.
            if case["id"] != "wrong-storage-type": db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
            for sql in case.get("after_rebuild_sql",[]): db.execute(sql)
            manifest["counts"]={t:db.execute("SELECT count(*) FROM "+t).fetchone()[0] for t in ("sources","chunks","relations")}
        data=work.read_bytes()
        if case.get("corrupt_header"): data=b"BROKEN HEADER!!!\x00"+data[16:]
        payloads["knowledge.sqlite"]=data
        manifest["files"]=[dict(path=p,sha256=sha(b),bytes=len(b),media_type="application/vnd.sqlite3" if p.endswith(".sqlite") else "application/octet-stream",required=True) for p,b in sorted(payloads.items())]
        raw=canonical(manifest); archive=run/(case["id"]+".kpack")
        with zipfile.ZipFile(archive,"w") as z:
            for name,data in sorted({**payloads,"manifest.json":raw,"manifest.sig":signer.sign(raw).signature}.items()):
                info=zipfile.ZipInfo(name,(1980,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100600<<16; z.writestr(info,data)
        records.append(dict(id=case["id"],filename=archive.name,accept=case["accept"],developer_mode=case.get("developer_mode",True),sha256=file_sha(archive),construction=case))
        # This is an owned transient fixture intermediate, not historical evidence.
        assert work.parent==run; work.unlink()
    (run/"cases.json").write_text(json.dumps(dict(cases=records,public_key_sha256=file_sha(run/"public-key.raw"),source_pack_sha256=file_sha(source),purpose="SIGNED_AUTHENTICATED_DB_NEGATIVES_NOT_REVIEWED_RELEASE_PROVENANCE",private_seed="EPHEMERAL_NOT_SAVED",script_sha256=file_sha(Path(__file__))),indent=2)+"\n",encoding="utf-8")
    asset.mkdir()
    for path in run.iterdir(): shutil.copyfile(path,asset/path.name)
    print("Frozen signed DB cases:",len(records))

if __name__=="__main__": main()
