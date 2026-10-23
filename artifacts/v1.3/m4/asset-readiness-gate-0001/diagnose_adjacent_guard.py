"""Preserve terminal failed suite, true completed originals and exact owner differences."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;run=ROOT/'artifacts/v1.3/m4/device-local-assets-adjacent-0001'
target=HERE/'adjacent-terminal-guard-diagnosis.json';assert not target.exists()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
manifest=read(run/'instrumentation-manifest.json');assert manifest['status']=='FAIL'
text=(run/'instrumentation.txt').read_text(encoding='utf-8');assert 'Tests run: 5,  Failures: 1' in text
match=re.search(r'expected:<\{(.*?)\}> but was:<\{(.*?)\}>',text);assert match
def values(value):
    rows=[row.rsplit('=',1) for row in value.split(', ')]
    assert all(len(row)==2 and re.fullmatch('[0-9a-f]{64}',row[1]) for row in rows)
    return dict(rows)
before,after=map(values,match.groups());assert len(before)==len(after)==50
delta={name:dict(before=before.get(name),after=after.get(name)) for name in before.keys()|after.keys() if before.get(name)!=after.get(name)}
adb=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR'];folder=run/'partial-collected-results';folder.mkdir(exist_ok=False)
files={
    'actualColdWarmAndNoPackDiagnosticsKeepOwnedContextAfterReaderClose':'m4-diagnostic-runtime.json',
    'nativeReplacementCancelRecoveryInspectionAndMutationKeepResultOwnership':'m4-diagnostic-lifecycle.json',
    'invalidAndNoPackInputsDoNotInitializeNativeGeneration':'m4-ui-query-inputs.json',
    'actualAnswerContextSurvivesInspectionAndMutationClearsDetails':'m4-source-details-viewmodel.json'}
saved={};commands=[];guards={}
for method,name in files.items():
    assert 'test='+method+'\nINSTRUMENTATION_STATUS_CODE: 0' in text.replace('\r',''),method
    argv=adb+['exec-out','run-as','org.packrag.product','cat','files/'+name]
    out=subprocess.run(argv,capture_output=True,check=True,timeout=30);data=json.loads(out.stdout);assert data['status']=='PASS'
    (folder/name).write_bytes(out.stdout);saved[name]=hashlib.sha256(out.stdout).hexdigest();guards[name]=data['owner_registry_and_model_sha256']
    commands.append(dict(argv=argv,returncode=out.returncode,stderr=out.stderr.decode('utf-8',errors='replace')))
# Save the failed method's phone file only as a stale-result comparison, not a new PASS.
argv=adb+['exec-out','run-as','org.packrag.product','cat','files/m4-ui-query-runtime.json']
out=subprocess.run(argv,capture_output=True,check=True,timeout=30);stale=run/'stale-query-runtime-after-failure.json';stale.write_bytes(out.stdout)
prior=ROOT/'artifacts/v1.3/m4/device-diagnostics-full-0001/original-adb/m4-ui-query-runtime.json'
parsed_equal=json.loads(out.stdout)==read(prior)
commands.append(dict(argv=argv,returncode=out.returncode,stderr=out.stderr.decode('utf-8',errors='replace')))
argv=adb+['logcat','-b','system','-d','-v','threadtime','-s','ActivityTaskManager:I','*:S']
out=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',errors='replace',check=True,timeout=30)
lines=[line for line in out.stdout.splitlines() if 'org.packrag.product' in line]
(HERE/'adjacent-guard-packrag-activity-log.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
commands.append(dict(argv=argv,returncode=out.returncode,filtered_rows=len(lines),scope='Only target-package activity rows retained; later logs do not independently identify a human actor or causality.'))
record=dict(status='FAIL_ADJACENT_OWNER_REGISTRY_BYTES_CHANGED_FOUR_METHOD_ORIGINALS_PRESERVED',recorded_utc=datetime.now(timezone.utc).isoformat(),
    methods=5,failures=1,whole_instrumentation_seconds=907.664,before_sha256=before,after_sha256=after,differences=delta,
    passing_original_sha256=saved,passing_method_guards=guards,commands=commands,
    failed_method_phone_file=dict(file=stale.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(stale.read_bytes()).hexdigest(),parsed_equal_to_prior_e3=parsed_equal,new_result_accepted=False),
    scope='Current suite stays FAIL. Only four completed JUnit-pass method originals saved. Guard difference does not prove logical-row changes or identify causal actor. Pre-change DB bytes were not captured; do not claim logical equivalence. No current test remains running; UI/policy/F2 are held until diagnosis and fresh retry.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status']);print(json.dumps(delta));print('Stale failed-method file equal to E3:',parsed_equal);print('Target activity log rows',len(lines))
