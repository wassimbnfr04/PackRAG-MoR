"""Preserve accepted execution iteration and exact two-test failure repair."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert read(HERE/'io-device-retry-execution.json')['status']=='PASS_E3_IO_AND_CONVERSION_RUNTIME_ORIGINAL_NOT_LIFECYCLE_OR_E3_CLOSURE'
audit=read(HERE/'io-preflight.json');run=M4/'device-diagnostics-0003';collector=read(run/'collected-results.json')
original=run/'original-adb/m4-diagnostic-runtime.json';assert sha(original)==collector['saved_sha256']['m4-diagnostic-runtime.json']
result=read(original);assert result==read(run/'m4-diagnostic-runtime.json') and len(result['cases'])==8
assert result['status']=='PASS' and all(r['passed'] for r in result['cases'])
for n,v in audit['build']['source_sha256'].items():assert sha(ROOT/n)==v,n
failed=read(M4/'build-0044/source-at-build-start.json')['files'];current=audit['build']['source_sha256']
assert failed.keys()==current.keys()
repair=[n for n in current if current[n]!=failed[n]]
assert set(repair)=={'product/android/app/src/test/java/org/packrag/product/BlockingIoTest.kt',
    'product/android/app/src/androidTest/java/org/packrag/product/DiagnosticRuntimeDeviceTest.kt'}
target=HERE/'io-iteration-sources';target.mkdir(exist_ok=False)
for n,v in audit['android_delta'].items():
    assert n.startswith('product/android/') and Path(n).suffix=='.kt'
    dest=target/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/n).read_bytes());assert sha(dest)==v
old=read(HERE/'io-device-guard-failure.json')['after_sha256'];now=result['owner_registry_and_model_sha256']
assert old==now,'New retry owner guard must bind the documented post-launch baseline'
(HERE/'io-iteration-acceptance.json').write_text(json.dumps(dict(status='PASS_E3_EXECUTION_AND_DIAGNOSTICS_ITERATION_NOT_COMPLETE_E3',
    build='build-0045',host_methods=50,android_inputs=569,device_methods=1,controls=8,junit_wall_seconds=290.365,
    original_sha256=sha(original),source_snapshots=audit['android_delta'],failed0044_exact_repair=repair,
    unchanged0044_other_inputs=len(current)-len(repair),python='run-0017',python_methods=1034,
    scope='Actual Default/IO wiring and two accepted cold/warm queries; exact owner guard within0003 at documented post-launch baseline. Original0002 default DB byte change remains FAIL; lifecycle/UI/fullpolicy/closure pending.'),indent=2)+'\n',encoding='utf-8')
print('PASS execution iteration, original, twelve source snapshots and exact two-test repair')
