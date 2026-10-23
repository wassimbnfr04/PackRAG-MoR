"""Full applicable current policy and development methods; originals before switches."""
import json,subprocess,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(HERE/'policy-diagnostics-execution.json')['status']=='PASS_E3_ACTUAL_COMPILED_POLICY_DIAGNOSTICS_ORIGINAL_NOT_COMPLETE_E3'
assert read(HERE/'retained-ui-resubmission-execution.json')['status']=='PASS_E3_FOUR_RETAINED_UI_ORIGINALS_NOT_COMPLETE_E3'
assert read(HERE/'retained-ui-visual.json')['status']=='PASS_E3_RETAINED_AR_FR_CANONICAL_TESTED_VIEWPORT'
source=read(M4/'build-0050/source-at-build-start.json')['files']
assert source==read(M4/'build-0051/source-at-build-start.json')['files']
for n,v in source.items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v,n
target=HERE/'full-background-execution.json';assert not target.exists();records=[];python=[sys.executable,'-X','utf8'];commands=[]
def add(build,run,prior,extra_classes,extra_files,variant='debug',timeout=5400):
    folder=M4/prior;classes=','.join(extra_classes)+','+read(folder/'instrumentation-manifest.json')['class_name']
    files=extra_files+list(read(folder/'collected-results.json')['saved_sha256']);assert len(files)==len(set(files))
    commands.append(python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/build),'--run',str(M4/run),
        '--class-name',classes,'--result-file',files[0],'--timeout',str(timeout),'--variant',variant])
    commands.append(python+['-m','scripts.v13_collect_phone_results','--run',str(M4/run),'--files',','.join(files)])
# Development first because retained UI just restored debug. Keep each original version.
add('build-0050','device-diagnostics-full-0001','device-source-details-full-0001',
    ['org.packrag.product.DiagnosticRuntimeDeviceTest','org.packrag.product.DiagnosticLifecycleDeviceTest'],
    ['m4-diagnostic-runtime.json','m4-diagnostic-lifecycle.json'])
add('build-0051','device-diagnostics-policy-full-0001','device-source-details-policy-full-0001',
    ['org.packrag.product.DiagnosticPolicyDeviceTest'],['m4-diagnostic-policy.json'],'demo')
commands.append(python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0050'),
    '--run',str(M4/'device-development-restore-0014'),'--class-name','org.packrag.product.PackImportConsentTest',
    '--result-file','m3-import-consent.json','--timeout','300'])
commands.append(python+['-m','scripts.v13_collect_phone_results','--run',str(M4/'device-development-restore-0014'),'--files','m3-import-consent.json'])
for i,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('E3 full background',i,'START',flush=True)
    with (HERE/f'full-background-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'full-background-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'Hold later milestones and preserve failure/completed originals before any repair or APK switch'
    print('E3 full background',i,'PASS',flush=True)
target.write_text(json.dumps(dict(status='PASS_E3_FULL_DEVELOPMENT_POLICY_RESTORATION_ORIGINALS_NOT_PARITY_OR_CLOSURE',commands=records),indent=2)+'\n',encoding='utf-8')
