"""Fresh residual-security corpus; private signing seeds are never persisted."""
import argparse
import copy
import json
import shutil
import struct
import zipfile
from pathlib import Path
from nacl.signing import SigningKey
from kpack_builder.core import canonical, key_id, sha
from product.packrag.config import file_sha

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--run",type=Path,required=True); args=parser.parse_args()
    run=args.run.resolve(); assert run.is_relative_to(ROOT); run.mkdir(parents=True,exist_ok=False)
    asset=ROOT/"product/android/app/src/androidTest/assets/security-corpus"; assert not asset.exists()
    source=ROOT/"artifacts/v1.3/m1/smoke-0001/developer-pack/walking-skeleton.kpack"
    with zipfile.ZipFile(source) as archive: original={n:archive.read(n) for n in archive.namelist()}
    base=json.loads(original.pop("manifest.json")); original.pop("manifest.sig")
    signer=SigningKey.generate(); public=bytes(signer.verify_key); (run/"public-key.raw").write_bytes(public)
    other=SigningKey.generate(); base["publisher"]["key_id"]=key_id(public); base["version"]="1.1.0"
    fleet=[bytes(SigningKey.generate().verify_key).hex() for _ in range(7)]+[public.hex()]
    records=[]
    def pack(identity,group,accept=False,contains=None,mutate=None,payload=None,redeclare=True,raw=None,signature=None,key=signer,omit_signature=False):
        manifest=copy.deepcopy(base); data=original.copy()
        if mutate: mutate(manifest)
        if payload:
            name,changed=payload; data[name]=changed
        if redeclare: manifest["files"]=[dict(path=n,sha256=sha(b),bytes=len(b),media_type="application/vnd.sqlite3" if n.endswith(".sqlite") else "application/octet-stream",required=True) for n,b in sorted(data.items())]
        signed=canonical(manifest) if raw is None else raw
        sig=key.sign(signed).signature if signature is None else signature
        entries={**data,"manifest.json":signed}
        if not omit_signature: entries["manifest.sig"]=sig
        path=run/(identity+".kpack")
        with zipfile.ZipFile(path,"w") as archive:
            for name,value in sorted(entries.items()):
                info=zipfile.ZipInfo(name,(1980,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100600<<16
                archive.writestr(info,value) # Fresh correct CRC, including deliberately changed payloads.
        records.append(dict(id=identity,group=group,filename=path.name,accept=accept,error_contains=contains,sha256=file_sha(path),manifest_sha256=sha(signed),payload_hashes_redeclared=redeclare))
        return signed,sig
    raw,sig=pack("valid","VALID",True)
    for name in ("knowledge.sqlite","dense.kdx"):
        changed=bytearray(original[name]); changed[-1]^=1
        pack("one-byte-"+name.replace(".","-"),"HASH_TAMPER",payload=(name,bytes(changed)),redeclare=False,contains="Payload hash")
    flipped=bytearray(sig); flipped[0]^=1
    pack("wrong-signature","AUTH_RAW",raw=raw,signature=bytes(flipped),contains="Unknown signer or invalid signature")
    pack("unknown-signer","AUTH_RAW",key=other,contains="Unknown signer or invalid signature")
    pack("wrong-message","AUTH_RAW",mutate=lambda m:m.update(domain="changed"),signature=sig,contains="Unknown signer or invalid signature")
    pack("missing-signature","AUTH_RAW",omit_signature=True)
    pack("broken-db-header","DB_STRUCTURAL",payload=("knowledge.sqlite",b"BROKEN HEADER!!!\0"+original["knowledge.sqlite"][16:]))
    def header(offset,fmt,value):
        data=bytearray(original["dense.kdx"]); struct.pack_into(fmt,data,offset,value); return bytes(data)
    variants={"magic":header(0,"<B",0),"version":header(8,"<H",2),"dtype":header(10,"<B",2),"metric":header(11,"<B",2),
              "dimension":header(12,"<H",385),"flags":header(14,"<H",0),"count":header(16,"<I",11),
              "profile-hash":header(20,"<B",original["dense.kdx"][20]^1),"mapping-hash":header(52,"<B",original["dense.kdx"][52]^1),
              "truncated":original["dense.kdx"][:-1],"extra-byte":original["dense.kdx"]+b"\0",
              "nan":header(84,"<f",float("nan")),"positive-infinity":header(84,"<f",float("inf")),"negative-infinity":header(84,"<f",-float("inf"))}
    for name,data in variants.items(): pack("kdx-"+name,"KDX_STRUCTURAL",payload=("dense.kdx",data),contains="KDX")
    for label,factor,accept in [("zero",0,False),("small",.8,False),("large",1.2,False),("near-low",.995,True),("near-high",1.005,True),("negative-unit",-1,True)]:
        data=bytearray(original["dense.kdx"])
        for i in range(384): struct.pack_into("<f",data,84+i*4,struct.unpack_from("<f",data,84+i*4)[0]*factor)
        pack("kdx-norm-"+label,"KDX_STRUCTURAL",accept,payload=("dense.kdx",bytes(data)),contains=None if accept else "KDX")
    for count in (255,256):
        pack("pack-id-"+str(count),"IDENTITY_BOUND",count==255,mutate=lambda m,c=count:m.update(pack_id="org."+"a"*(c-4)),contains=None if count==255 else "portable installation component")
        pack("version-"+str(count),"IDENTITY_BOUND",count==255,mutate=lambda m,c=count:m.update(version="1.0.0+"+"a"*(c-6)),contains=None if count==255 else "portable installation component")
    for depth in (33,4096):
        nested=raw[:-1]+b',"x":'+b"["*(depth-1)+b"0"+b"]"*(depth-1)+b"}"
        pack("json-depth-"+str(depth),"JSON_BOUND",raw=nested,contains="nesting limit")
    pack("noncanonical-signed","JSON_CANONICAL",raw=raw+b"\n",contains="Noncanonical signed manifest")
    raw_vectors=[]
    def vector(name,message,accept,contains=None,signature=None):
        raw_vectors.append(dict(id=name,raw_hex=message.hex(),signature_hex=(signer.sign(message).signature if signature is None else signature).hex(),accept=accept,error_contains=contains))
    vector("valid-manifest",raw,True)
    for depth in (32,33,4096):
        message=canonical(dict(publisher=dict(key_id=key_id(public))))[:-1]+b',"x":'+b"["*(depth-1)+b"0"+b"]"*(depth-1)+b"}"
        vector("signed-depth-"+str(depth),message,depth==32,None if depth==32 else "nesting limit")
    quoted=canonical(dict(publisher=dict(key_id=key_id(public)),x='["\\]}'*4096)); vector("quoted-brackets-escapes",quoted,True)
    vector("unknown-before-depth",bytes.fromhex(raw_vectors[3]["raw_hex"]),False,"Unknown signer or invalid signature",bytes(flipped))
    vector("malformed-utf8",b"\xff",False)
    vector("duplicate-json-keys",b'{"publisher":{"key_id":"'+key_id(public).encode()+b'"},"x":1,"x":2}',False,"Noncanonical signed manifest")
    bounds=[dict(id="array-depth-"+str(d),raw="["*d+"0"+"]"*d,accept=d<=32) for d in (1,31,32,33,4096)]
    for label,value,accept in [("quoted-depth",json.dumps('['*4096+']'*4096),True),("escaped-quote",json.dumps({'x':'\\"[}]'}),True),
                               ("scalar","42",True),("unbalanced","[}",False),("unterminated-array","[0",False),("unterminated-string",'"x\\',False)]:
        bounds.append(dict(id=label,raw=value,accept=accept))
    (run/"raw-vectors.json").write_text(json.dumps(dict(public_key_hex=public.hex(),eight_distinct_public_keys_hex=fleet,cases=raw_vectors),indent=2)+"\n",encoding="utf-8")
    (run/"bounds-cases.json").write_text(json.dumps(bounds,indent=2)+"\n",encoding="utf-8")
    (run/"cases.json").write_text(json.dumps(dict(cases=records,public_key_sha256=file_sha(run/"public-key.raw"),source_pack_sha256=file_sha(source),
        purpose="SIGNED_RESIDUAL_SECURITY_SYNTHETIC_NOT_RELEASE_CALIBRATION",private_seed="EPHEMERAL_NOT_SAVED",max_json_depth=32,portable_identity_component_bytes=255,script_sha256=file_sha(Path(__file__))),indent=2)+"\n",encoding="utf-8")
    asset.mkdir()
    for path in run.iterdir(): shutil.copyfile(path,asset/path.name)
    print("Frozen security packs:",len(records),"raw signature vectors:",len(raw_vectors),"JSON bound cases:",len(bounds))

if __name__=="__main__": main()
