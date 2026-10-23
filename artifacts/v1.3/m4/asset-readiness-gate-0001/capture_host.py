"""Save exact tested F1 source bytes and public artifacts for a completed build."""
import argparse,hashlib,json,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);args=parser.parse_args()
build=ROOT/'artifacts/v1.3/m4'/args.build;assert build.parent==ROOT/'artifacts/v1.3/m4'
target=HERE/(args.build+'-host-capture.json');assert not target.exists()
result=read(build/'build-result.json');assert result['exit_code']==0
sources=read(build/'source-at-build-start.json')['files']
for name,value in sources.items():assert sha(ROOT/name)==value,name
suites=[ET.parse(p).getroot() for p in (build/'host-tests').rglob('TEST-*.xml')]
totals={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ['tests','failures','errors','skipped']}
assert totals==dict(tests=62,failures=0,errors=0,skipped=0)
prior=read(HERE/'preimplementation.json')['android_source_sha256']
delta={name:value for name,value in sources.items() if prior.get(name)!=value}
for name,value in delta.items():
    p=HERE/(args.build+'-tested-sources')/name;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists()
    p.write_bytes((ROOT/name).read_bytes());assert sha(p)==value
record=dict(status='PASS_TESTED_F1_HOST_BYTES_NOT_DEVICE_OR_F1_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    build=args.build,variant=result['variant'],android_inputs=len(sources),host_totals=totals,tested_source_sha256=delta,
    apk_sha256={p.name:sha(p) for p in build.glob('*.apk')},build_result_sha256=sha(build/'build-result.json'),
    scope='Host unit/contracts/regressions and completed APK build only. Actual device/native/UI and full milestone gates remain independent. Existing analytics/Kotlin-daemon access warnings may use documented fallback; terminal result is authoritative.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'],len(delta),'changed sources')
