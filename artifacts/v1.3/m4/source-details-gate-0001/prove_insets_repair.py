"""Exact layout delta and bounded reuse of unchanged Python/desktop evidence."""
import hashlib,json
from datetime import datetime,timezone
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
target=HERE/'insets-repair-proof.json';assert not target.exists()
repair=read(HERE/'insets-repair.json');assert len(repair['changes'])==2
bindings={}
for earlier,later,variant in [('build-0039','build-0041','debug'),('build-0040','build-0042','demo')]:
    a=read(M4/earlier/'source-at-build-start.json')['files'];b=read(M4/later/'source-at-build-start.json')['files']
    assert a.keys()==b.keys() and len(b)==561 and {n for n in a if a[n]!=b[n]}==set(repair['changes'])
    for name,value in b.items():assert sha(ROOT/name)==value,name
    for name,values in repair['changes'].items():
        old=(HERE/'insets-repair-before'/name).read_bytes();current=(ROOT/name).read_bytes()
        assert hashlib.sha256(old).hexdigest()==a[name]==values['old_sha256']
        assert hashlib.sha256(current).hexdigest()==b[name]==values['new_sha256']
        newline=b'\r\n' if b'\r\n' in old else b'\n';import_needle=b'import androidx.compose.foundation.layout.padding'+newline
        needle=b'Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp))'
        assert old.count(import_needle)==old.count(needle)==1
        assert current==old.replace(import_needle,import_needle+b'import androidx.compose.foundation.layout.safeDrawingPadding'+newline).replace(
            needle,b'Column(Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(24.dp))')
    bindings[variant]=dict(earlier_build=earlier,final_build=later,unchanged_other_android_inputs=len(a)-2,
        earlier_product_apk_sha256=sha(M4/earlier/f'app-{variant}.apk'),final_product_apk_sha256=sha(M4/later/f'app-{variant}.apk'),
        reuse='No old Android run promoted; repaired host/UI/full-device/policy/restoration required')
assert read(M4/'build-0041/source-at-build-start.json')['files']==read(M4/'build-0042/source-at-build-start.json')['files']
spec=spec_from_file_location('e2_desktop_reuse_no_main',HERE/'verify_new_results.py');module=module_from_spec(spec);spec.loader.exec_module(module)
desktop=module.desktop();assert desktop['runtime_inputs']==188
assert sha(HERE/'visual-inspection.json')==repair['visual_failure_sha256']
assert read(HERE/'visual-inspection.json')['status'].startswith('FAIL_')
target.write_text(json.dumps(dict(status='PASS_EXACT_TWO_SOURCE_UI_INSETS_REPAIR_UNCHANGED_PYTHON_DESKTOP_NOT_REPAIRED_UI_OR_E2_ACCEPTANCE',
    recorded_utc=datetime.now(timezone.utc).isoformat(),bindings=bindings,desktop=desktop,
    original_visual_failure_preserved=True,limits='Python1034 and six desktop gates retained under their actual unchanged188 source identities, not claimed reruns. Product layout/APKs changed.'),indent=2)+'\n',encoding='utf-8')
print('Exact two-source insets repair/559 unchanged other inputs/188 Python+desktop inputs verified')
