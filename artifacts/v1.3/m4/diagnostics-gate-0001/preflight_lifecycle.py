"""Current lifecycle iteration audit with exact retained-source/result custody."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(values):
    for n,v in values.items():assert sha(ROOT/n)==v,n
target=HERE/'lifecycle-preflight.json';assert not target.exists()
gate=read(M4/'source-details-gate-0001/gate.json');check(gate['source_sha256']);check(gate['output_sha256'])
history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];check(history)
for label in ['first','io']:
    record=read(HERE/(label+'-iteration-acceptance.json'))
    folder='first-iteration-sources' if label=='first' else 'io-iteration-sources'
    for n,v in record['source_snapshots'].items():assert sha(HERE/folder/n)==v,n
    device='device-diagnostics-0001' if label=='first' else 'device-diagnostics-0003'
    assert sha(M4/device/'original-adb/m4-diagnostic-runtime.json')==record['original_sha256']
python=read(M4/'run-0017/result-manifest.json');assert python['totals']==dict(tests=1034,failures=0,errors=0,skipped=0)
assert {n:v for n,v in python['source_sha256'].items() if n not in ['PLAN.md','STATUS.md','DECISIONS.md']}==gate['source_sha256']
original=M4/'source-details-gate-0001/preflight_repaired.py';assert sha(original)==gate['output_sha256'][original.relative_to(ROOT).as_posix()]
source=original.read_text(encoding='utf-8');before='dict(tests=40,failures=0,errors=0,skipped=0)'
assert source.count(before)==1;derived=source.replace(before,'dict(tests=53,failures=0,errors=0,skipped=0)')
env={'__name__':'e3_lifecycle_audit_no_old_main','__file__':str(Path(__file__).resolve())}
exec(compile(derived,str(original)+'#e3-lifecycle-audit','exec'),env)
build=env['audit']('build-0046','debug','lifecycle-debug');current=build['source_sha256'];assert len(current)==573
record=dict(status='PASS_E3_LIFECYCLE_HOST_SOURCE_HISTORY_APK_NOT_DEVICE_OR_UI_OR_COMPLETE_E3',recorded_utc=datetime.now(timezone.utc).isoformat(),
    build=build,android_inputs=len(current),android_delta={n:v for n,v in current.items() if gate['android_source_sha256'].get(n)!=v},
    python_inputs=188,python_methods=1034,e2_public_outputs_unchanged=len(gate['output_sha256']),historical_unchanged=len(history),
    original_audit_sha256=sha(original),derived_audit_sha256=hashlib.sha256(derived.encode('utf-8')).hexdigest(),
    scope='Same APK/trust/native/no-INTERNET/input assertions with host total53; prior iteration source snapshots/originals unchanged. Actual lifecycle/foreground/visual/fullregression/policy/closure still required.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
