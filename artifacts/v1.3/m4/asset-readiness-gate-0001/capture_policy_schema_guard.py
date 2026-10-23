"""Preserve the checker failure, bind legacy report schemas and read final policy guards."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'policy-schema-and-owner-guard-0001.json';assert not target.exists()
driver=read(HERE/'policy-and-restoration-execution-0001.json');assert driver['status']=='FAIL' and len(driver['commands'])==4 and driver['commands'][-1]['returncode']==1
assert 'KeyError: \'owner_registry_and_model_sha256\'' in (HERE/'policy-restoration-0001-stage-3.stderr.txt').read_text()
run=M4/'device-local-assets-policy-adjacent-0001';manifest=read(run/'instrumentation-manifest.json');collection=read(run/'collected-results.json')
assert manifest['status']==collection['status']=='PASS' and manifest['variant']=='demo'
assert manifest['apk_sha256']==collection['apk_sha256']==read(HERE/'corrected-pair-preflight.json')['apk_sha256']['build-0057']
assert 'OK (3 tests)' in (run/'instrumentation.txt').read_text() and 'FAILURES' not in (run/'instrumentation.txt').read_text()
assert not (M4/'device-local-assets-development-restore-0001').exists()
e3=read(M4/'diagnostics-gate-0001/gate.json');inputs=read(M4/'build-0057/source-at-build-start.json')['files'];assert len(inputs)==579
schemas={}
for name,source in [('m4-ui-query-policy.json','QueryControlsPolicyTest.kt'),('m4-source-details-policy.json','SourceDetailsPolicyTest.kt')]:
    old=M4/'device-diagnostics-policy-full-0001/original-adb'/name;fresh=run/'original-adb'/name
    assert sha(old)==e3['output_sha256'][old.relative_to(ROOT).as_posix()] and sha(fresh)==collection['saved_sha256'][name]
    before=read(old);after=read(fresh);assert set(before)==set(after) and after['compiled_developer_mode'] is False
    assert after['status']=='PASS' and all(row['passed'] is True for row in after['cases'])
    assert 'owner_registry_and_model_sha256' not in before and 'owner_registry_and_model_sha256' not in after
    relative='product/android/app/src/androidTest/java/org/packrag/product/'+source
    assert inputs[relative]==e3['android_source_sha256'][relative]==sha(ROOT/relative)
    schemas[name]=dict(original_sha256=sha(fresh),prior_original_sha256=sha(old),exact_key_set=sorted(after),
        test_source=relative,test_source_sha256=inputs[relative],missing_owner_guard=True,missing_network_mode='network_mode' not in after,
        scope='Exact unchanged accepted E3 schema; no fields added to the original. Final whole-phase public guard below is independent, not an in-method assertion for this report.')
expected=read(HERE/'guarded-retry-preparation.json')['owner_public_file_sha256'];assert len(expected)==50
assert all(re.fullmatch(r'[A-Za-z0-9_.@/-]+',name) and '.private' not in Path(name).parts for name in expected)
argv=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell','run-as','org.packrag.product','sha256sum',*['files/'+name for name in sorted(expected)]]
out=subprocess.run(argv,capture_output=True,check=True,timeout=60);observed={}
for line in out.stdout.decode('utf-8').splitlines():
    value,name=line.split(maxsplit=1);assert re.fullmatch('[0-9a-f]{64}',value) and name.startswith('files/');observed[name[6:]]=value
assert observed==expected==read(run/'original-adb/m4-diagnostic-policy.json')['owner_registry_and_model_sha256']
record=dict(status='PASS_ACTUAL_POLICY_PHASE_FINAL_OWNER_GUARD_AND_UNCHANGED_LEGACY_SCHEMA_NOT_CLOSURE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    failure_scope='Report checker KeyError, after all three actual phone methods and original collection passed. Sequence stopped before development restoration. No phone test, APK, source or original report was changed.',
    failed_driver_sha256=sha(HERE/'policy-and-restoration-execution-0001.json'),failed_checker_source_sha256=sha(HERE/'verify-background-first-policy-attempt.py.txt'),
    actual_failure_stderr_sha256=sha(HERE/'policy-restoration-0001-stage-3.stderr.txt'),legacy_report_contracts=schemas,
    owner_public_file_sha256=observed,guarded_file_count=50,commands=[dict(argv=argv,returncode=out.returncode,stdout=out.stdout.decode('utf-8'),stderr=out.stderr.decode('utf-8',errors='replace'))],
    scope='Read exactly known50 public paths after completed policy adjacent phase and before any restoration/install. DiagnosticPolicy original independently contains the same before/after phase baseline. Two legacy methods do not assert individual owner equality; this sidecar is not claimed as such. No private custody, model export, data reset or radio modification. Missing network metadata is not invented: compiled APK no-INTERNET identity is separately checked.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
