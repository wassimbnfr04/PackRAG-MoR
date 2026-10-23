"""Preserve actual new policy original and test source while retained UI runs."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert read(HERE/'policy-diagnostics-execution.json')['status']=='PASS_E3_ACTUAL_COMPILED_POLICY_DIAGNOSTICS_ORIGINAL_NOT_COMPLETE_E3'
run=M4/'device-diagnostic-policy-0001';saved=read(run/'collected-results.json')['saved_sha256'];original=run/'original-adb/m4-diagnostic-policy.json'
assert sha(original)==saved[original.name];data=read(original);assert len(data['cases'])==8 and all(r['passed'] for r in data['cases'])
assert data['status']=='PASS' and data['compiled_developer_mode'] is False and data['actual_weight_inference'] and data['build_type']=='demo'
sources=read(M4/'build-0049/source-at-build-start.json')['files']
for n,v in sources.items():assert sha(ROOT/n)==v,n
name='product/android/app/src/androidTest/java/org/packrag/product/DiagnosticPolicyDeviceTest.kt';p=HERE/'policy-iteration-sources'/name
assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
target=HERE/'policy-iteration-acceptance.json';assert not target.exists()
record=dict(status='PASS_E3_APPROVED_NATIVE_COMPILED_POLICY_ITERATION_NOT_COMPLETE_E3',recorded_utc=datetime.now(timezone.utc).isoformat(),
    build='build-0049',host_methods=53,android_inputs=574,device_methods=1,controls=8,junit_wall_seconds=311.814,
    original_sha256=sha(original),source_snapshots={name:sha(p)},
    scope='Actual ViewModel build-owned trust/native generation/diagnostic ownership/rejection and owner-file guard. Instrumentable debug-signed demo, schema-only synthetic fixture; not final release, measured calibration, final content or performance. Full regressions/parity/restoration/closure pending.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
message='E3 current10 October19:52 UTC: actual compiled-policy diagnostics0001 PASSES one method/eight controls311.814s; original33b3b260ea1abb03af5f613bf3e1f7462c175fae0b619fa0423e6084d695fde9 saved before switch. Real approved-signer ViewModel cold/warm/native/inspection/abstention/mutation/developer rejection and owner guards pass. Desktop0016 all14 pass. Retained four-method UI is starting on byte-identical debug0048 after fresh awake/unlocked observations and announced five-minute untouched window. Collect four originals/two AR/FR PNGs and actually inspect before full37/30 background/restoration/parity/closure. No F/later progression. Mobile data stays on, final content owner supplied.\n\n'
status=ROOT/'STATUS.md';text=status.read_text(encoding='utf-8-sig');status.write_text(text.replace('# PackRAG-MoR v1.3 status\n\n','# PackRAG-MoR v1.3 status\n\n'+message,1),encoding='utf-8')
for doc in ['docs/v1.3/M4E3_METHODS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md']:
    with (ROOT/doc).open('a',encoding='utf-8') as f:f.write('\n\n'+message)
print(record['status'])
