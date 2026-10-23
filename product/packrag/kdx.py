"""KDX structure/profile/vector checks precede SQLite; row binding follows validated DB."""
import math
import struct
from kpack_builder.core import canonical, sha
from .errors import require

HEADER=struct.Struct('<8sHBBHHI32s32s')
VECTOR=struct.Struct('<384f')

def inspect_kdx(path,profile,count):
    require(path.stat().st_size==84+count*384*4,'KDX count/size mismatch')
    with path.open('rb') as stream:
        raw=stream.read(84); require(len(raw)==84,'Truncated KDX header')
        magic,version,dtype,metric,dim,flags,n,ph,mh=HEADER.unpack(raw)
        require((magic,version,dtype,metric,dim,flags)==(b'KDX1\0\0\0\0',1,1,1,384,1),'Invalid KDX header')
        require(n==count,'KDX count/size mismatch')
        require(ph==bytes.fromhex(sha(canonical(profile))),'KDX profile/mapping hash mismatch')
        for _ in range(count):
            raw=stream.read(VECTOR.size); require(len(raw)==VECTOR.size,'KDX count/size mismatch')
            values=VECTOR.unpack(raw); require(all(math.isfinite(v) for v in values),'Nonfinite KDX vector')
            # Ascending component order with double accumulation matches Android.
            require(abs(math.sqrt(sum(v*v for v in values))-1)<=.01,'KDX vector norm mismatch')
        require(not stream.read(1),'KDX count/size mismatch')
    return mh.hex()

def verify_mapping(mapping_hash,ids):
    require(mapping_hash==sha(canonical(ids)),'KDX profile/mapping hash mismatch')
