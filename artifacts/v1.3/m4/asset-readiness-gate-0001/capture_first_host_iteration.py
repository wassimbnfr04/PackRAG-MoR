"""Preserve successful first host iteration before additional F1 device coverage."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'first-host-iteration.json';assert not target.exists()
build=ROOT/'artifacts/v1.3/m4/build-0054';assert read(build/'build-result.json')['exit_code']==0
sources=read(build/'source-at-build-start.json')['files'];assert len(sources)==577
for name,expected in sources.items():assert sha(ROOT/name)==expected,name
suites=[ET.parse(path).getroot() for path in (build/'host-tests').rglob('TEST-*.xml')]
totals={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ['tests','failures','errors','skipped']}
assert totals==dict(tests=62,failures=0,errors=0,skipped=0)
prior=read(HERE/'preimplementation.json')['android_source_sha256'];delta={name:value for name,value in sources.items() if prior.get(name)!=value}
assert len(delta)==6
for name,value in delta.items():
    path=HERE/'first-host-sources'/name;path.parent.mkdir(parents=True,exist_ok=True);assert not path.exists()
    path.write_bytes((ROOT/name).read_bytes());assert sha(path)==value
target.write_text(json.dumps(dict(status='PASS_FIRST_F1_VERIFIER_HOST_ITERATION_NOT_DEVICE_OR_COMPLETE_F1',recorded_utc=datetime.now(timezone.utc).isoformat(),
    build='build-0054',android_inputs=577,host_totals=totals,source_snapshots=delta,apk_sha256={path.name:sha(path) for path in build.glob('*.apk')},
    scope='Real host verifier contracts and retained host regressions. Physical readiness/native/UI and full F acceptance remain pending. Gradle metrics/Kotlin daemon permission warnings used the existing compiler fallback; terminal build succeeds. No source changed during this build.'),indent=2)+'\n',encoding='utf-8')
print('Actual577-source/62-host first F1 iteration saved; device coverage and full increment acceptance pending')
