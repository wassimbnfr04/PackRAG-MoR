"""Audit the new execution iteration; no accepted output is overwritten."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(values):
    for name,value in values.items():assert sha(ROOT/name)==value,name
target=HERE/'io-preflight.json';assert not target.exists()
gate=read(M4/'source-details-gate-0001/gate.json');check(gate['source_sha256']);check(gate['output_sha256'])
history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];check(history)
first=read(HERE/'first-iteration-acceptance.json')
for name,value in first['source_snapshots'].items():assert sha(HERE/'first-iteration-sources'/name)==value,name
assert sha(M4/'device-diagnostics-0001/original-adb/m4-diagnostic-runtime.json')==first['original_sha256']
original=M4/'source-details-gate-0001/preflight_repaired.py'
assert sha(original)==gate['output_sha256'][original.relative_to(ROOT).as_posix()]
source=original.read_text(encoding='utf-8');before='dict(tests=40,failures=0,errors=0,skipped=0)'
assert source.count(before)==1;derived=source.replace(before,'dict(tests=50,failures=0,errors=0,skipped=0)')
env={'__name__':'e3_io_audit_no_old_main','__file__':str(Path(__file__).resolve())}
exec(compile(derived,str(original)+'#e3-io-audit','exec'),env)
build=env['audit']('build-0044','debug','io-debug')
current=build['source_sha256'];baseline=gate['android_source_sha256']
assert baseline.keys()<=current.keys();assert len(current)==569
record=dict(status='PASS_E3_IO_HOST_SOURCE_HISTORY_APK_NOT_DEVICE_OR_COMPLETE_E3',
    recorded_utc=datetime.now(timezone.utc).isoformat(),build=build,runtime_inputs=len(gate['source_sha256']),
    android_inputs=len(current),android_delta={n:v for n,v in current.items() if baseline.get(n)!=v},
    e2_public_outputs_unchanged=len(gate['output_sha256']),historical_unchanged=len(history),first_sources_unchanged=len(first['source_snapshots']),
    original_audit_sha256=sha(original),derived_audit_sha256=hashlib.sha256(derived.encode('utf-8')).hexdigest(),
    scope='Same APK/trust/native/no-INTERNET/input checks with host total50; first iteration source snapshots/original remain immutable. New device dispatch/conversion checks still required.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
