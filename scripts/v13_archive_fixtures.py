"""Freeze ZIP transport fixtures around one authentic, bounded synthetic pack."""
import argparse
import copy
import json
import shutil
import struct
import zipfile
import zlib
from pathlib import Path
from nacl.signing import SigningKey
from kpack_builder.core import canonical, key_id, sha
from product.packrag.config import file_sha

ROOT = Path(__file__).resolve().parents[1]


def archive(entries, *, method=8, descriptor=0, local64=False, mutation=None, comment=b""):
    local = bytearray(); central = bytearray()
    for index, (name, payload) in enumerate(entries):
        raw = name.encode("utf-8"); flags = 0x800 | (8 if descriptor else 0); version = 45 if local64 else 20
        compressed = payload if method == 0 else zlib.compress(payload)[2:-4]
        crc = zlib.crc32(payload); sizes = (len(compressed), len(payload)); start = len(local)
        extra = struct.pack("<HHQQ",1,16,len(payload),len(compressed)) if local64 else b""
        lc = bytearray(struct.pack("<IHHHHHIIIHH",0x04034b50,version,flags,method,0,33,0 if descriptor else crc,
            0xffffffff if local64 else (0 if descriptor else sizes[0]),0xffffffff if local64 else (0 if descriptor else sizes[1]),len(raw),len(extra)))
        cc = bytearray(struct.pack("<IHHHHHHIIIHHHHHII",0x02014b50,0x0314,version,flags,method,0,33,crc,*sizes,len(raw),0,0,0,0,0o100600<<16,start))
        lraw = raw; craw = raw; cextra = b""; data = compressed; suffix = b""
        if descriptor:
            suffix = (b"PK\x07\x08" if descriptor == 1 else b"") + struct.pack("<IQQ" if local64 else "<III",crc,*sizes)
        if mutation and index == 0:
            kind = mutation
            if kind == "local-name": lraw = b"X"+raw[1:]
            elif kind == "invalid-utf8": craw = lraw = b"\xff"+raw[1:]
            elif kind == "missing-utf8": struct.pack_into("<H",lc,6,flags & ~0x800); struct.pack_into("<H",cc,8,flags & ~0x800)
            elif kind == "local-flags": struct.pack_into("<H",lc,6,flags ^ 8)
            elif kind == "local-method": struct.pack_into("<H",lc,8,0)
            elif kind == "local-version": struct.pack_into("<H",lc,4,10)
            elif kind == "local-crc": struct.pack_into("<I",lc,14,crc ^ 1)
            elif kind == "local-compressed": struct.pack_into("<I",lc,18,sizes[0]+1)
            elif kind == "local-size": struct.pack_into("<I",lc,22,sizes[1]+1)
            elif kind == "central-size": struct.pack_into("<I",cc,24,256*1024*1024+1)
            elif kind == "central-compressed": struct.pack_into("<I",cc,20,513*1024*1024+1)
            elif kind == "central-local-offset": struct.pack_into("<I",cc,42,1)
            elif kind == "disk-entry": struct.pack_into("<H",cc,34,1)
            elif kind == "symlink": struct.pack_into("<I",cc,38,0o120600<<16)
            elif kind == "directory-bit": struct.pack_into("<I",cc,38,(0o100600<<16)|0x10)
            elif kind == "encryption": struct.pack_into("<H",lc,6,flags|1); struct.pack_into("<H",cc,8,flags|1)
            elif kind == "unknown-flag": struct.pack_into("<H",lc,6,flags|0x10); struct.pack_into("<H",cc,8,flags|0x10)
            elif kind == "unknown-method": struct.pack_into("<H",lc,8,12); struct.pack_into("<H",cc,10,12)
            elif kind == "unknown-version": struct.pack_into("<H",lc,4,99); struct.pack_into("<H",cc,6,99)
            elif kind == "short-extra": extra = cextra = b"\x99"
            elif kind == "duplicate-extra": extra = cextra = struct.pack("<HHHH",0x5455,0,0x5455,0)
            elif kind == "aes-extra": extra = cextra = struct.pack("<HH",0x9901,0)
            elif kind == "zip64-central": cextra = struct.pack("<HH",1,0)
            elif kind == "unicode-extra-mismatch": extra = cextra = struct.pack("<HHBI",0x7075,6,1,zlib.crc32(raw))+b"x"
            elif kind == "unicode-extra-valid": extra = cextra = struct.pack("<HHBI",0x7075,5+len(raw),1,zlib.crc32(raw))+raw
            elif kind == "timestamp-extra": extra = cextra = struct.pack("<HHBI",0x5455,5,1,1700000000)
            elif kind == "descriptor-crc": suffix = suffix[:4]+bytes([suffix[4]^1])+suffix[5:]
            elif kind == "descriptor-size": suffix = suffix[:-1]+bytes([suffix[-1]^1])
            elif kind == "hidden-gap": suffix += b"HIDDEN"
            elif kind == "crc-payload": data = bytes([data[0]^1])+data[1:]
            elif kind == "central-crc-payload":
                struct.pack_into("<I",lc,14,crc ^ 1); struct.pack_into("<I",cc,16,crc ^ 1)
            else: raise ValueError(kind)
        struct.pack_into("<H",lc,28,len(extra)); struct.pack_into("<H",cc,30,len(cextra))
        local += lc+lraw+extra+data+suffix; central += cc+craw+cextra
    end = struct.pack("<IHHHHIIH",0x06054b50,0,0,len(entries),len(entries),len(central),len(local),len(comment))
    return bytes(local+central+end+comment)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--run",type=Path,required=True); args=parser.parse_args()
    run=args.run.resolve(); assert run.is_relative_to(ROOT); run.mkdir(parents=True,exist_ok=False)
    asset=ROOT/"product/android/app/src/androidTest/assets/archive-corpus"; assert not asset.exists()
    source=ROOT/"artifacts/v1.3/m1/smoke-0001/developer-pack/walking-skeleton.kpack"
    with zipfile.ZipFile(source) as z: original={name:z.read(name) for name in z.namelist()}
    base=json.loads(original.pop("manifest.json")); original.pop("manifest.sig")
    signer=SigningKey.generate(); public=bytes(signer.verify_key); (run/"public-key.raw").write_bytes(public)
    records=[]
    def add(identifier, accept, *, names=(), method=8, descriptor=0, local64=False, mutation=None, comment=b"", edit=None, audit_accept=None):
        manifest=copy.deepcopy(base); manifest["publisher"]["key_id"]=key_id(public); payloads=original.copy()
        for name in names: payloads[name]=b"Synthetic transport fixture; not a release source."
        manifest["files"]=[dict(path=p,sha256=sha(b),bytes=len(b),media_type="application/vnd.sqlite3" if p.endswith(".sqlite") else "application/octet-stream",required=True) for p,b in sorted(payloads.items())]
        raw=canonical(manifest); entries=list(sorted(payloads.items()))+[("manifest.json",raw),("manifest.sig",signer.sign(raw).signature)]
        if names: entries.sort(key=lambda pair: 0 if pair[0] == names[0] else 1)
        data=archive(entries,method=method,descriptor=descriptor,local64=local64,mutation=mutation,comment=comment)
        if edit: data=edit(data)
        output=run/(identifier+".kpack"); output.write_bytes(data)
        records.append(dict(id=identifier,filename=output.name,accept=accept,audit_accept=accept if audit_accept is None else audit_accept,sha256=file_sha(output),construction=dict(names=names,method=method,descriptor=descriptor,local_zip64=local64,mutation=mutation,edited=bool(edit))))
    for method in (0,8):
        add(f"valid-method-{method}",True,method=method)
        for descriptor in (1,2):
            add(f"valid-descriptor-{method}-{descriptor}",True,method=method,descriptor=descriptor)
        add(f"valid-local64-{method}",True,method=method,local64=True)
        add(f"valid-local64-descriptor-{method}",True,method=method,local64=True,descriptor=1)
    add("valid-comment",True,comment=b"Transport comment does not alter semantic pack identity.")
    for mutation in ("unicode-extra-valid","timestamp-extra"): add(mutation,True,mutation=mutation)
    add("valid-unicode",True,names=("sources/é.txt","sources/文.txt","sources/😀.txt","sources/\ue000.txt"))
    for mutation in ("local-name","invalid-utf8","local-flags","local-method","local-version","local-crc","local-compressed","local-size","central-size","central-compressed","central-local-offset","disk-entry","symlink","directory-bit","encryption","unknown-flag","unknown-method","unknown-version","short-extra","duplicate-extra","aes-extra","zip64-central","unicode-extra-mismatch","hidden-gap"):
        add(mutation,False,mutation=mutation)
    add("missing-utf8",False,names=("sources/é.txt",),mutation="missing-utf8")
    for mutation in ("descriptor-crc","descriptor-size"): add(mutation,False,descriptor=1,mutation=mutation)
    add("crc-payload",False,method=0,mutation="crc-payload",audit_accept=True)
    add("central-crc-payload",False,mutation="central-crc-payload",audit_accept=True)
    add("truncated",False,edit=lambda b:b[:-1]); add("appended-bytes",False,edit=lambda b:b+b"x")
    add("prefixed-bytes",False,edit=lambda b:b"x"+b)
    add("split-disk",False,edit=lambda b:b[:-18]+struct.pack("<H",1)+b[-16:])
    for identifier, names in {
        "case-duplicate":("sources/A.txt","sources/a.txt"),"full-fold-duplicate":("sources/ß.txt","sources/ss.txt"),"sigma-duplicate":("sources/ς.txt","sources/σ.txt"),"ligature-duplicate":("sources/ﬀ.txt","sources/ff.txt"),
        "traversal":("sources/../escape.txt",),"absolute":("/sources/a.txt",),"backslash":("sources/a\\b.txt",),"drive":("sources/C:a.txt",),"dos":("sources/CON.txt",),"decomposed":("sources/e\u0301.txt",),"trailing-dot":("sources/a.",),"trailing-space":("sources/a ",),"control":("sources/a\u007f.txt",),"empty-segment":("sources//a.txt",),"long-segment":("sources/"+"a"*256+".txt",),"script":("sources/a.vbs",),"model":("sources/a.gguf",),"outside-sources":("a.txt",)
    }.items(): add(identifier,False,names=names)
    (run/"cases.json").write_text(json.dumps(dict(cases=records,public_key_sha256=file_sha(run/"public-key.raw"),source_pack_sha256=file_sha(source),purpose="SYNTHETIC_SIGNED_ZIP_TRANSPORT_AND_IMPORT_GATE",private_seed="EPHEMERAL_NOT_SAVED",script_sha256=file_sha(Path(__file__))),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    asset.mkdir()
    for path in run.iterdir(): shutil.copyfile(path,asset/path.name)
    print("Frozen ZIP cases:",len(records))

if __name__=="__main__": main()
