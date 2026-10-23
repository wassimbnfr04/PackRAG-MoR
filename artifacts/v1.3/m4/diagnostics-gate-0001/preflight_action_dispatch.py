"""New final matched pair; precisely two test helper deltas from0050/51."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(values):
    for n,v in values.items():assert sha(ROOT/n)==v,n
target=HERE/'action-dispatch-preflight.json';assert not target.exists()
repair=read(HERE/'ui-action-dispatch-repair.json');gate=read(M4/'source-details-gate-0001/gate.json')
check(gate['source_sha256']);check(gate['output_sha256']);history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];check(history)
original=M4/'source-details-gate-0001/preflight_repaired.py';assert sha(original)==gate['output_sha256'][original.relative_to(ROOT).as_posix()]
source=original.read_text(encoding='utf-8');before='dict(tests=40,failures=0,errors=0,skipped=0)';assert source.count(before)==1
env={'__name__':'e3_action_dispatch_audit_no_main','__file__':str(Path(__file__).resolve())}
exec(compile(source.replace(before,'dict(tests=53,failures=0,errors=0,skipped=0)'),str(original)+'#action-dispatch-audit','exec'),env)
debug=env['audit']('build-0052','debug','dispatch-final-debug');policy=env['audit']('build-0053','demo','dispatch-final-demo')
a=debug['source_sha256'];assert a==policy['source_sha256'] and len(a)==574
old=read(M4/'build-0050/source-at-build-start.json')['files'];deltas=repair['exact_test_deltas']
assert set(a)==set(old) and {n for n in a if a[n]!=old[n]}==set(deltas)
for n,v in deltas.items():
    assert a[n]==v['after'] and old[n]==v['before'] and sha(HERE/'ui-action-dispatch-before'/Path(n).name)==v['before']
product_identity={}
for build,previous,variant in [('build-0052','build-0048','debug'),('build-0053','build-0049','demo')]:
    p=M4/build/('app-'+variant+'.apk');assert sha(p)==sha(M4/previous/p.name);product_identity[build]=sha(p)
assert read(HERE/'resubmission-preflight.json')['status']=='PASS_E3_TEST_ONLY_RESUBMISSION_MATCHED_PAIR_NOT_DEVICE_ACCEPTANCE'
for run in ['device-ui-diagnostics-retained-0001','device-ui-diagnostics-retained-0002','device-ui-diagnostics-retained-0003']:
    record=read(M4/run/'partial-collected-results.json')
    for n,v in record['original_sha256'].items():assert sha(M4/run/'original-adb'/n)==v,n
for label in ['first','io','navigation','policy']:
    row=read(HERE/(label+'-iteration-acceptance.json'))
    for n,v in row['source_snapshots'].items():assert sha(HERE/(label+'-iteration-sources')/n)==v,n
py=read(M4/'run-0017/result-manifest.json');assert py['totals']==dict(tests=1034,failures=0,errors=0,skipped=0)
assert {n:v for n,v in py['source_sha256'].items() if n not in ['PLAN.md','STATUS.md','DECISIONS.md']}==gate['source_sha256']
target.write_text(json.dumps(dict(status='PASS_E3_TEST_ONLY_ACTION_DISPATCH_MATCHED_PAIR_NOT_DEVICE_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    builds=[debug,policy],exact_test_deltas=deltas,unchanged_android_inputs=572,byte_identical_product_apk=product_identity,
    python_methods=1034,immutable_e2_outputs=len(gate['output_sha256']),historical_inputs=len(history),
    scope='Fresh pair574 inputs/53 host each. Only two test helper synchronization changes. Product is byte-identical0048/49; prior actual policy/navigation selected sources unchanged. Fresh all-four UI/visual/full37/full30/restore/parity/closure still required.'),indent=2)+'\n',encoding='utf-8')
print('PASS two exact test deltas/574 inputs/53 host each/unchanged product APKs/history')
