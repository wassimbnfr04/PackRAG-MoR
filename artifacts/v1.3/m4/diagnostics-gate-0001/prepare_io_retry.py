"""Exact same tested APK/source/class; only new run/output paths for the retry."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert read(HERE/'io-device-execution.json')['status']=='FAIL'
assert read(HERE/'io-device-guard-failure.json')['new_structured_result_written'] is False
assert read(HERE/'python-retry-execution.json')['status']=='PASS_FULL_E3_PYTHON_HOST_PERMISSION_RETRY_NOT_COMPLETE_E3'
python=read(M4/'run-0017/result-manifest.json');assert python['totals']==dict(tests=1034,failures=0,errors=0,skipped=0)
old=read(M4/'source-details-gate-0001/gate.json')
current={n:v for n,v in python['source_sha256'].items() if n not in ['PLAN.md','STATUS.md','DECISIONS.md']}
assert current==old['source_sha256']
audit=read(HERE/'io-preflight.json')
for n,v in audit['build']['source_sha256'].items():assert sha(ROOT/n)==v,n
for n,v in audit['build']['apk_sha256'].items():assert sha(M4/'build-0045'/n)==v,n
for n,v in old['output_sha256'].items():assert sha(ROOT/n)==v,n
source=HERE/'run_io_device.py';text=source.read_text();replacements={
    'io-device-execution.json':'io-device-retry-execution.json','device-diagnostics-0002':'device-diagnostics-0003',
    'io-stage-':'io-retry-stage-'}
for before,after in replacements.items():assert text.count(before)==(2 if before=='io-stage-' else 1);text=text.replace(before,after)
target=HERE/'run_io_retry_device.py';assert not target.exists();target.write_text(text,encoding='utf-8')
(HERE/'io-retry-preparation.json').write_text(json.dumps(dict(status='PASS_UNCHANGED_0045_SOURCE_APKS_AND_PYTHON_RETRY_NOT_DEVICE',
    original_driver_sha256=sha(source),new_driver_sha256=sha(target),only_output_replacements=replacements,
    apk_sha256=audit['build']['apk_sha256'],android_inputs=len(audit['build']['source_sha256']),python_inputs=len(current),
    unchanged_e2_outputs=len(old['output_sha256']),scope='Exact same class,timeout,variant,build,assertions; only fresh output paths. Failed0002 and stale prior JSON remain preserved.'),indent=2)+'\n',encoding='utf-8')
print('PASS same0045 source/APKs and1034 Python; fresh0003 retry prepared')
