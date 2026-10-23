"""Final matched source variants, retained byte-exact UI and policy-fixture provenance."""
import hashlib,json,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(values):
    for n,v in values.items():assert sha(ROOT/n)==v,n
target=HERE/'policy-diagnostics-preflight.json';assert not target.exists()
assert read(HERE/'navigation-visual-repaired.json')['status']=='PASS_REPAIRED_DIAGNOSTIC_AND_CANONICAL_TESTED_VIEWPORT'
gate=read(M4/'source-details-gate-0001/gate.json');check(gate['source_sha256']);check(gate['output_sha256'])
history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];check(history)
original=M4/'source-details-gate-0001/preflight_repaired.py';assert sha(original)==gate['output_sha256'][original.relative_to(ROOT).as_posix()]
source=original.read_text(encoding='utf-8');before='dict(tests=40,failures=0,errors=0,skipped=0)';assert source.count(before)==1
derived=source.replace(before,'dict(tests=53,failures=0,errors=0,skipped=0)')
env={'__name__':'e3_policy_audit_no_old_main','__file__':str(Path(__file__).resolve())};exec(compile(derived,str(original)+'#e3-policy-audit','exec'),env)
debug=env['audit']('build-0048','debug','policy-diag-debug');policy=env['audit']('build-0049','demo','policy-diag-demo')
current=debug['source_sha256'];assert current==policy['source_sha256'] and len(current)==574
old=read(M4/'build-0047/source-at-build-start.json')['files'];new='product/android/app/src/androidTest/java/org/packrag/product/DiagnosticPolicyDeviceTest.kt'
assert set(current)-set(old)=={new} and all(current[n]==v for n,v in old.items())
assert sha(M4/'build-0048/app-debug.apk')==sha(M4/'build-0047/app-debug.apk')
for label in ['first','io','navigation']:
    record=read(HERE/(label+'-iteration-acceptance.json'));folder=HERE/(label+'-iteration-sources')
    for n,v in record['source_snapshots'].items():assert sha(folder/n)==v,n
for run in ['device-diagnostics-0001','device-diagnostics-0003','device-diagnostic-lifecycle-0001','device-ui-diagnostic-navigation-0001','device-ui-diagnostic-navigation-0002']:
    saved=read(M4/run/'collected-results.json')['saved_sha256']
    for n,v in saved.items():assert sha(M4/run/'original-adb'/n)==v,n
    if 'navigation' in run:
        for n,row in read(M4/run/'m4-diagnostic-navigation.json')['visual_png'].items():assert sha(M4/run/'original-adb'/n)==row['sha256']
fixture=read(HERE/'policy-diagnostics-preparation.json')['fixture'];asset=ROOT/'product/android/app/src/androidTest/assets/release-trust-corpus'/fixture['filename']
assert sha(asset)==fixture['sha256']
with zipfile.ZipFile(M4/'build-0049/app-demo-androidTest.apk') as archive:
    assert hashlib.sha256(archive.read('assets/release-trust-corpus/'+asset.name)).hexdigest()==fixture['sha256']
py=read(M4/'run-0017/result-manifest.json');assert py['totals']==dict(tests=1034,failures=0,errors=0,skipped=0)
assert {n:v for n,v in py['source_sha256'].items() if n not in ['PLAN.md','STATUS.md','DECISIONS.md']}==gate['source_sha256']
record=dict(status='PASS_E3_MATCHED_POLICY_PAIR_NOT_ACTUAL_POLICY_OR_FULL_E3',recorded_utc=datetime.now(timezone.utc).isoformat(),
    builds=[debug,policy],new_test_sha256=current[new],unchanged0047_inputs=573,byte_identical_debug_product_sha256=sha(M4/'build-0048/app-debug.apk'),
    retained_ui='Actual0047 repaired UI and actual0046 lifecycle retained by exact source and product APK byte equality; never relabelled reruns.',
    python_methods=1034,python_public_inputs=188,immutable_e2_outputs=len(gate['output_sha256']),historical_inputs=len(history),
    scope='Fresh instrumentable debug/demo53 host each; actual new approved-signer policy diagnostics/full retained regressions/parity/restoration/closure still pending. Schema-only fixture is not genuine calibration.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
