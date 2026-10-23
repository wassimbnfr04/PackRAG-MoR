"""Test-only capture repair; exact product bytes and572 other source inputs."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(values):
    for n,v in values.items():assert sha(ROOT/n)==v,n
target=HERE/'capture-repair-preflight.json';assert not target.exists()
gate=read(M4/'source-details-gate-0001/gate.json');check(gate['source_sha256']);check(gate['output_sha256'])
history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];check(history)
assert read(HERE/'navigation-visual-initial.json')['status']=='FAIL_HOME_DIAGNOSTIC_MEASUREMENTS_NOT_VISIBLE_SOURCE_CANONICAL_VISIBLE'
assert read(HERE/'lifecycle-device-execution.json')['status']=='PASS_E3_REAL_NATIVE_LIFECYCLE_ORIGINAL_NOT_FOREGROUND_OR_COMPLETE_E3'
for device,name in [('device-diagnostic-lifecycle-0001','m4-diagnostic-lifecycle.json'),('device-ui-diagnostic-navigation-0001','m4-diagnostic-navigation.json')]:
    saved=read(M4/device/'collected-results.json')['saved_sha256'];assert sha(M4/device/'original-adb'/name)==saved[name]
for n,row in read(M4/'device-ui-diagnostic-navigation-0001/m4-diagnostic-navigation.json')['visual_png'].items():
    assert sha(M4/'device-ui-diagnostic-navigation-0001/original-adb'/n)==row['sha256']
original=M4/'source-details-gate-0001/preflight_repaired.py';assert sha(original)==gate['output_sha256'][original.relative_to(ROOT).as_posix()]
source=original.read_text(encoding='utf-8');before='dict(tests=40,failures=0,errors=0,skipped=0)'
assert source.count(before)==1;derived=source.replace(before,'dict(tests=53,failures=0,errors=0,skipped=0)')
env={'__name__':'e3_capture_audit_no_old_main','__file__':str(Path(__file__).resolve())}
exec(compile(derived,str(original)+'#e3-capture-repair-audit','exec'),env)
build=env['audit']('build-0047','debug','capture-repaired-debug')
old=read(M4/'build-0046/source-at-build-start.json')['files'];current=build['source_sha256'];assert old.keys()==current.keys() and len(current)==573
changed=[n for n in current if old[n]!=current[n]]
expected='product/android/app/src/androidTest/java/org/packrag/product/DiagnosticNavigationUiTest.kt';assert changed==[expected]
assert sha(HERE/'DiagnosticNavigationUiTest-before-capture-repair.kt')==old[expected]
old_apk=sha(M4/'build-0046/app-debug.apk');assert sha(M4/'build-0047/app-debug.apk')==old_apk
record=dict(status='PASS_EXACT_PRODUCT_APK_SINGLE_UI_CAPTURE_REPAIR_NOT_NEW_UI_VISUAL_OR_E3_CLOSURE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    build=build,changed_android_inputs=changed,unchanged_other_android_inputs=572,product_apk_sha256=old_apk,
    e2_public_outputs_unchanged=len(gate['output_sha256']),historical_unchanged=len(history),
    retained_lifecycle='Original0046 actual lifecycle203.706s retains original version/scope under exact unchanged source and product APK proof; not rerun.',
    scope='Fresh53 host/573 inputs/native/trust/no-INTERNET; capture-only hide-IME and actual displayed count/timing checks. New actual foreground/PNG/visual review required; initial automated PASS/visualFAIL stays unchanged.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
