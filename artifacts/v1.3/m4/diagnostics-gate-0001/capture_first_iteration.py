"""Preserve tested first-iteration source bytes before the adjacent repair."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert read(HERE/'minimal-device-execution.json')['status']=='PASS_E3_FIRST_DIAGNOSTIC_RUNTIME_AND_ORIGINAL_NOT_LIFECYCLE_DISPATCH_OR_E3_CLOSURE'
audit=read(HERE/'minimal-preflight.json');run=M4/'device-diagnostics-0001'
collector=read(run/'collected-results.json');assert collector['status']=='PASS'
original=run/'original-adb/m4-diagnostic-runtime.json'
assert sha(original)==collector['saved_sha256']['m4-diagnostic-runtime.json']
result=read(original);assert result==read(run/'m4-diagnostic-runtime.json')
assert result['status']=='PASS' and len(result['cases'])==6 and all(r['passed'] for r in result['cases'])
for name,value in audit['build']['source_sha256'].items():assert sha(ROOT/name)==value,name
target=HERE/'first-iteration-sources';target.mkdir(exist_ok=False)
for name,value in audit['android_delta'].items():
    assert name.startswith('product/android/') and Path(name).suffix=='.kt'
    dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
    assert sha(dest)==value
(HERE/'first-iteration-acceptance.json').write_text(json.dumps(dict(
    status='PASS_FIRST_INTEGRATED_DIAGNOSTIC_ITERATION_NOT_COMPLETE_E3',build='build-0043',
    tests=1,cases=6,junit_wall_seconds=289.615,original_sha256=sha(original),
    source_snapshots=audit['android_delta'],scope='Actual two accepted cold/warm queries; ownership/inspection/no-pack controls. Dispatch/lifecycle/accessibility/full-policy acceptance still pending.'),indent=2)+'\n',encoding='utf-8')
print('PASS first diagnostic iteration, original and nine source snapshots')
