"""Read-only public historical APK size/dedup feasibility, not final packaging."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
target=HERE/'apk-size-audit.json';assert not target.exists()
files=[]
for name in ('m0','m1','m2','m3','m4'):
    for build in (ROOT/'artifacts/v1.3'/name).glob('build-*'):
        if build.is_dir():files.extend(sorted(build.glob('*.apk')))
assert files
records=[];blocks4={};blocks64={}
for path in files:
    assert path.resolve().is_relative_to(ROOT) and '.private' not in path.parts
    whole=hashlib.sha256();count=0
    with path.open('rb') as stream:
        while data:=stream.read(65536):
            whole.update(data);count+=len(data);blocks64.setdefault(hashlib.sha256(data).hexdigest(),len(data))
            for offset in range(0,len(data),4096):
                part=data[offset:offset+4096];blocks4.setdefault(hashlib.sha256(part).hexdigest(),len(part))
    assert count==path.stat().st_size
    records.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=count,sha256=whole.hexdigest()))
record=dict(status='READ_ONLY_PUBLIC_APK_FEASIBILITY_NOT_FINAL_PACKAGE_OR_RUNTIME_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),public_apk_files=len(files),total_original_apk_bytes=sum(r['bytes'] for r in records),unique_64k_block_bytes=sum(blocks64.values()),unique_64k_blocks=len(blocks64),unique_4k_block_bytes=sum(blocks4.values()),unique_4k_blocks=len(blocks4),files=records,
    scope='Only top-level APKs in versioned m0-m4 build directories; no temporary/cache/model/export/private custody traversal. Reads originals without mutation; saves hashes/counts, never block payloads.',
    limits=['No final ZIP or block reassembler is implemented by this size audit','Counts model potential identical SHA256-addressed block reuse, not actual archive compression/ZIP overhead or byte-reconstruction validation','Future final APKs/reports/packs/source are additional; actual three ZIP sizes and reconstruction must be measured and verified at final packaging','Private custody and model weights/diagnostic exports remain excluded by owner instruction'])
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:record[k] for k in ('status','public_apk_files','total_original_apk_bytes','unique_64k_block_bytes','unique_4k_block_bytes','unique_4k_blocks')}))
