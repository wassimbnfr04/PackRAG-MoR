"""Application-owned approved public publisher configuration; no pack key admission."""
import json
import re
from pathlib import Path
from kpack_builder.core import key_id
from .errors import require
from .json_bounds import bounded_structure

def trusted_publishers(value):
    require(type(value) is dict and set(value)=={"schema_version","approval_scope","publishers"},"Trust store fields mismatch")
    require(value["schema_version"]=="1.0" and value["approval_scope"]=="packrag-project-demonstrators","Unsupported trust store")
    publishers=value["publishers"]
    require(type(publishers) is list and 1<=len(publishers)<=8,"Trust store must contain 1–8 approved publishers")
    keys=[]
    for publisher in publishers:
        require(type(publisher) is dict and set(publisher)=={"name","key_id","public_key_hex"},"Publisher fields mismatch")
        require(type(publisher["name"]) is str and bool(publisher["name"].strip()),"Invalid publisher name")
        encoded=publisher["public_key_hex"]
        require(type(encoded) is str and re.fullmatch(r"[0-9a-f]{64}",encoded),"Invalid publisher public key")
        key=bytes.fromhex(encoded)
        require(publisher["key_id"]==key_id(key),"Publisher key identity mismatch")
        keys.append(key)
    require(len(set(keys))==len(keys),"Duplicate approved publisher")
    return tuple(keys)

def load_trust(path: Path):
    require(0<path.stat().st_size<=64*1024,"Trust store exceeds bounded configuration size")
    raw=path.read_bytes(); bounded_structure(raw)
    def unique_object(pairs):
        result={}
        for key,value in pairs:
            require(key not in result,"Duplicate trust store property"); result[key]=value
        return result
    return trusted_publishers(json.loads(raw.decode("utf-8",errors="strict"),object_pairs_hook=unique_object))
