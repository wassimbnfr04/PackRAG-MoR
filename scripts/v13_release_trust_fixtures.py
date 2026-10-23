"""Project-signed schema-only admission vectors, never measured release calibration."""
import argparse
import copy
import json
import shutil
import zipfile
from pathlib import Path
from nacl.signing import SigningKey
from kpack_builder.core import canonical,key_id,sha
from product.packrag.config import file_sha
from product.packrag.trust import load_trust

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--run",type=Path,required=True); args=parser.parse_args()
    run=args.run.resolve(); assert run.is_relative_to(ROOT); run.mkdir(parents=True,exist_ok=False)
    assets=ROOT/"product/android/app/src/androidTest/assets/release-trust-corpus"; assert not assets.exists()
    store=ROOT/"product/config/release-trust.json"; approved=load_trust(store)
    signer=SigningKey((ROOT/"product/.private/demo-publisher.seed").read_bytes()); public=bytes(signer.verify_key); assert public in approved
    source=ROOT/"artifacts/v1.3/m1/smoke-0001/developer-pack/walking-skeleton.kpack"
    with zipfile.ZipFile(source) as archive: payload={n:archive.read(n) for n in archive.namelist()}
    base=json.loads(payload.pop("manifest.json")); payload.pop("manifest.sig")
    base.update(pack_id="org.packrag.test.release-policy",name="SYNTHETIC TRUST TEST — NOT RELEASE CALIBRATION",version="0.0.1+fixture")
    base["publisher"]=dict(name="PackRAG project demonstrator publisher",key_id=key_id(public))
    base["build"]["builder_version"]="1.3.0-trust-security-fixture"
    base["calibration"]=dict(status="CALIBRATED",dataset_sha256=sha(b"SCHEMA_ONLY_NO_MEASURED_CALIBRATION"),method="candidate-relevance-v1.3",min_agreed_dense_cosine=.5,min_dense_only_cosine=.8,precision=.9,recall=.8)
    other=SigningKey.generate(); cases=[]
    def archive(identity,accept,contains=None,mutate=None,key=signer):
        manifest=copy.deepcopy(base)
        if mutate: mutate(manifest)
        raw=canonical(manifest); files={**payload,"manifest.json":raw,"manifest.sig":key.sign(raw).signature}; path=run/(identity+".kpack")
        with zipfile.ZipFile(path,"w") as output:
            for name,data in sorted(files.items()):
                info=zipfile.ZipInfo(name,(1980,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100600<<16; output.writestr(info,data)
        cases.append(dict(id=identity,filename=path.name,accept_production=accept,error_contains=contains,sha256=file_sha(path),manifest_sha256=sha(raw)))
    archive("calibration-schema-only",True)
    archive("known-publisher-uncalibrated",False,"Uncalibrated pack requires developer mode",lambda m:m.update(calibration=dict(status="UNCALIBRATED",dataset_sha256=None,method="candidate-relevance-v1.3",min_agreed_dense_cosine=None,min_dense_only_cosine=None,precision=None,recall=None)))
    archive("unknown-publisher",False,"Unknown signer or invalid signature",key=other)
    archive("pack-cannot-add-key",False,"Manifest fields mismatch",lambda m:m["publisher"].update(trusted_keys=[bytes(other.verify_key).hex()]))
    archive("claimed-key-mismatch",False,"Signer/key_id mismatch",lambda m:m["publisher"].update(key_id=key_id(bytes(other.verify_key))))
    value=json.loads(store.read_text()); vectors=[dict(id="one-approved-format",accept=True,value=value)]
    fleet=json.loads((ROOT/"artifacts/v1.3/m3/security-fixtures-0001/raw-vectors.json").read_text())["eight_distinct_public_keys_hex"]
    eight=copy.deepcopy(value); eight["publishers"]=[dict(name="FORMAT FIXTURE ONLY",key_id=key_id(bytes.fromhex(x)),public_key_hex=x) for x in fleet]; vectors.append(dict(id="eight-distinct-format-not-runtime-approval",accept=True,value=eight))
    for label,mutate in [
        ("empty",lambda m:m.update(publishers=[])),("nine",lambda m:m.update(publishers=eight["publishers"]+[eight["publishers"][0]])),
        ("duplicate",lambda m:m.update(publishers=[m["publishers"][0]]*2)),("wrong-id",lambda m:m["publishers"][0].update(key_id="ed25519:"+"0"*64)),
        ("short-key",lambda m:m["publishers"][0].update(public_key_hex="0"*62)),("uppercase-key",lambda m:m["publishers"][0].update(public_key_hex=m["publishers"][0]["public_key_hex"].upper())),
        ("numeric-name",lambda m:m["publishers"][0].update(name=42)),("blank-name",lambda m:m["publishers"][0].update(name=" ")),
        ("unapproved-scope",lambda m:m.update(approval_scope="arbitrary-third-party")),("extra-root",lambda m:m.update(extra=True)),
        ("extra-publisher",lambda m:m["publishers"][0].update(private_seed="NOT_A_SECRET_TEST_SENTINEL")),("missing-key",lambda m:m["publishers"][0].pop("public_key_hex")),
        ("non-array",lambda m:m.update(publishers={})),("wrong-schema",lambda m:m.update(schema_version="2.0"))]:
        candidate=copy.deepcopy(value); mutate(candidate); vectors.append(dict(id=label,accept=False,value=candidate))
    (run/"store-cases.json").write_text(json.dumps(vectors,indent=2)+"\n",encoding="utf-8")
    (run/"cases.json").write_text(json.dumps(dict(cases=cases,approved_store_sha256=file_sha(store),source_pack_sha256=file_sha(source),purpose="SYNTHETIC_RELEASE_TRUST_AND_CALIBRATION_SCHEMA_ONLY_NOT_REAL_CALIBRATION",private_seed="LOCAL_CUSTODY_NOT_EXPORTED",ephemeral_unknown_seed="NOT_SAVED",script_sha256=file_sha(Path(__file__))),indent=2)+"\n",encoding="utf-8")
    assets.mkdir()
    for path in run.iterdir(): shutil.copyfile(path,assets/path.name)
    print("Frozen production admission cases:",len(cases),"public-store format cases:",len(vectors))

if __name__=="__main__": main()
