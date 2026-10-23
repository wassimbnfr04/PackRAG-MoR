"""Source-bound E3 diagnostic iteration audit using the accepted APK audit."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(values):
    for name,value in values.items():assert sha(ROOT/name)==value,name
target=HERE/'minimal-preflight.json';assert not target.exists()
gate=read(M4/'source-details-gate-0001/gate.json');check(gate['source_sha256']);check(gate['output_sha256'])
history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];check(history)
original=M4/'source-details-gate-0001/preflight_repaired.py'
assert sha(original)==gate['output_sha256'][original.relative_to(ROOT).as_posix()]
source=original.read_text(encoding='utf-8');before='dict(tests=40,failures=0,errors=0,skipped=0)'
assert source.count(before)==1;derived=source.replace(before,'dict(tests=47,failures=0,errors=0,skipped=0)')
env={'__name__':'e3_minimal_audit_no_old_main','__file__':str(Path(__file__).resolve())}
exec(compile(derived,str(original)+'#e3-minimal-audit','exec'),env)
build=env['audit']('build-0043','debug','minimal-debug')
current=build['source_sha256'];baseline=gate['android_source_sha256']
assert baseline.keys()<=current.keys();assert len(current)==567
record=dict(status='PASS_E3_MINIMAL_SOURCE_HOST_HISTORY_APK_NOT_DEVICE_OR_E3_ACCEPTANCE',
    recorded_utc=datetime.now(timezone.utc).isoformat(),build=build,runtime_inputs=len(gate['source_sha256']),
    android_inputs=len(current),android_delta={n:v for n,v in current.items() if baseline.get(n)!=v},
    e2_public_outputs_unchanged=len(gate['output_sha256']),historical_unchanged=len(history),
    original_audit_sha256=sha(original),derived_audit_sha256=hashlib.sha256(derived.encode('utf-8')).hexdigest(),
    statement='Only audit host total changes from40 to47; the same source/APK/trust/native/no-INTERNET/test-asset assertions run in the new E3 folder. No old audit/output is overwritten.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
