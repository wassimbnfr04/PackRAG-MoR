"""Bind unchanged product/Python/desktop evidence to the exact scrolling-test repair."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
target=HERE/'test-only-repair-proof.json';assert not target.exists()
repair=read(HERE/'ui-test-repair.json');path=ROOT/repair['source']
old=(HERE/'PackManagementUiTest-before-status-scroll.kt').read_bytes()
assert hashlib.sha256(old).hexdigest()==repair['old_sha256']
needle=b'compose.onNodeWithText("NO_ACTIVE_PACK").assertIsDisplayed()'
assert old.count(needle)==1 and path.read_bytes()==old.replace(needle,b'compose.onNodeWithText("NO_ACTIVE_PACK").performScrollTo().assertIsDisplayed()')
bindings={}
for earlier,later,variant in [('build-0033','build-0035','debug'),('build-0034','build-0036','demo')]:
    a=read(M4/earlier/'source-at-build-start.json')['files'];b=read(M4/later/'source-at-build-start.json')['files'];assert a.keys()==b.keys()
    assert {n for n in a if a[n]!=b[n]}=={repair['source']}
    assert a[repair['source']]==repair['old_sha256'] and b[repair['source']]==repair['new_sha256']
    for name,value in b.items():assert digest(ROOT/name)==value,name
    product=digest(M4/earlier/f'app-{variant}.apk');assert product==digest(M4/later/f'app-{variant}.apk')
    bindings[variant]=dict(earlier_build=earlier,final_build=later,unchanged_product_apk_sha256=product,unchanged_other_inputs=len(a)-1,
        earlier_test_apk_sha256=digest(M4/earlier/f'app-{variant}-androidTest.apk'),final_test_apk_sha256=digest(M4/later/f'app-{variant}-androidTest.apk'))
runtime=read(M4/'selection-gate-0002/gate.json')['source_sha256']
regression=read(M4/'run-0014/result-manifest.json');desktop=read(M4/'existing-walking-smoke-0013/inputs.json')
assert {n:v for n,v in regression['source_sha256'].items() if n not in ['PLAN.md','STATUS.md','DECISIONS.md']}==runtime
assert desktop['source_sha256']==runtime
for name,value in runtime.items():assert digest(ROOT/name)==value,name
assert regression['status']=='PASS' and read(M4/'existing-walking-smoke-0013/smoke-results.json')['status']=='PASS'
target.write_text(json.dumps(dict(status='PASS_EXACT_TEST_SCROLL_REPAIR_PRODUCT_IDENTICAL_RETAINED_RUNTIME_EVIDENCE_NOT_A_RERUN',
    bindings=bindings,runtime_inputs_unchanged=len(runtime),retained_python_run='run-0014',retained_desktop_run='existing-walking-smoke-0013',
    final_ui='Requires actual fresh0003 both methods and original results; initial0001 partial is not substituted',
    limits='Retains only unchanged runtime/product tests under their actual recorded identities; whole E1 physical/policy/restoration/closure still required'),indent=2)+'\n')
old_runner=(HERE/'run_device_gates_repaired.py').read_bytes();new_runner=old_runner.decode('utf-8').replace("'ui-execution-0002.json'","'ui-execution-0003.json'")
assert new_runner!=old_runner.decode('utf-8')
destination=HERE/'run_device_gates_final.py';assert not destination.exists();destination.write_text(new_runner,encoding='utf-8');compile(new_runner,str(destination),'exec')
(HERE/'final-device-runner-derivation.json').write_text(json.dumps(dict(original='run_device_gates_repaired.py',new=destination.name,
    original_sha256=hashlib.sha256(old_runner).hexdigest(),new_sha256=digest(destination),only_change='Require fresh successful UI0003 rather than preflight-failed0002'),indent=2)+'\n')
print('Exact test-only repair, product bytes and185 retained runtime inputs verified')
