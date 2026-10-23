"""Read raw Git blob bytes in a batch; no filesystem or index mutation on import."""
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def git(*args,check=True,input=None):
    return subprocess.run(['git','-c','safe.directory='+ROOT.as_posix(),'-c','core.autocrlf=false',*args],
        cwd=ROOT,input=input,capture_output=True,check=check)
def blobs(ref,names):
    assert ref in ['HEAD','']
    assert all(not any(c in name for c in ['\n','\r','\0']) for name in names)
    raw=git('cat-file','--batch',input=b''.join((ref+':'+name+'\n').encode('utf-8') for name in names)).stdout
    offset=0;result={}
    for name in names:
        end=raw.find(b'\n',offset);assert end>=offset
        header=raw[offset:end];offset=end+1
        if header.endswith(b' missing'):
            assert header==(ref+':'+name+' missing').encode('utf-8')
            result[name]=None;continue
        object_id,kind,size=header.rsplit(b' ',2)
        assert len(object_id) in [40,64] and kind==b'blob' and size.isdigit()
        length=int(size);assert offset+length<len(raw) and raw[offset+length:offset+length+1]==b'\n'
        result[name]=raw[offset:offset+length];offset+=length+1
    assert offset==len(raw)
    return result
