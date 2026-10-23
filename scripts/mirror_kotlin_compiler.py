"""Mirror the pinned compiler from Maven Central into a local Maven repository."""
import hashlib
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
relative='org/jetbrains/kotlin/kotlin-compiler-embeddable/2.4.20/'
directory=ROOT/'vendor/maven'/relative
directory.mkdir(parents=True,exist_ok=True)
base='https://repo.maven.apache.org/maven2/'+relative
for suffix in ['pom','jar']:
    name='kotlin-compiler-embeddable-2.4.20.'+suffix
    target=directory/name
    with urllib.request.urlopen(base+name+'.sha1',timeout=30) as response:expected=response.read().decode().strip().split()[0]
    existing=hashlib.sha1(target.read_bytes()).hexdigest() if target.exists() else None
    if existing!=expected:
        print('Downloading',name,flush=True)
        # The host download proxy stalled on an unbounded GET of this large jar.
        # Bounded standard HTTP range requests also make incomplete files explicit.
        with urllib.request.urlopen(urllib.request.Request(base+name,method='HEAD'),timeout=30) as response:size=int(response.headers['Content-Length'])
        partial=target.with_suffix(target.suffix+'.partial')
        mirror='https://maven-central.storage-download.googleapis.com/maven2/'+relative
        def segment(start):
            end=min(size-1,start+1024*1024-1)
            request=urllib.request.Request(mirror+name+f'?packrag_range={start}',headers={'Range':f'bytes={start}-{end}'})
            with urllib.request.urlopen(request,timeout=30) as response:
                data=response.read(end-start+2)
                assert len(data)==end-start+1,'Incomplete compiler range'
                if size>1024*1024:
                    assert response.status==206,'Server ignored range'
                    assert response.headers['Content-Range']==f'bytes {start}-{end}/{size}','Incorrect compiler range'
                return data
        with partial.open('wb') as output,ThreadPoolExecutor(6) as pool:
            for index,data in enumerate(pool.map(segment,range(0,size,1024*1024))):
                output.write(data)
                if index%8==0:print('Verified download bytes',output.tell(),'/',size,flush=True)
        partial.replace(target)
    with target.open('rb') as stream:actual=hashlib.file_digest(stream,'sha1').hexdigest()
    assert expected==actual,'Upstream compiler checksum mismatch'
    print(name,target.stat().st_size,actual,flush=True)
