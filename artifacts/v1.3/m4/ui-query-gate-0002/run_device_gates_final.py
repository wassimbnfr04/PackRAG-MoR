"""Complete E1/retained gates, originals before switches, restore development on success."""
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(HERE/'ui-execution-0003.json')['status']=='PASS_TWO_FOREGROUND_METHODS_ORIGINALS_SAVED'
assert read(HERE/'preflight-repaired.json')['status'].startswith('PASS_')
assert read(HERE/'regression-execution.json')['status']=='PASS_FULL_PYTHON_AND_RETAINED_DESKTOP_WALKING'
python=[sys.executable,'-X','utf8'];commands=[]
def gate(build,run,classes,files,variant='debug',timeout=4500):
    commands.append(python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/build),'--run',str(M4/run),
        '--class-name',classes,'--result-file',files[0],'--timeout',str(timeout),'--variant',variant])
    commands.append(python+['-m','scripts.v13_collect_phone_results','--run',str(M4/run),'--files',','.join(files)])
gate('build-0035','device-query-controls-0001','org.packrag.product.QueryControlsDeviceTest',['m4-ui-query-runtime.json','m4-ui-query-inputs.json'],timeout=1800)
prior=read(M4/'device-selection-full-0002/instrumentation-manifest.json')
gate('build-0035','device-query-regression-0001',prior['class_name'],list(read(M4/'device-selection-full-0002/collected-results.json')['saved_sha256']))
prior=read(M4/'device-production-selection-0001/instrumentation-manifest.json')
gate('build-0036','device-query-policy-0001','org.packrag.product.QueryControlsPolicyTest,'+prior['class_name'],
    ['m4-ui-query-policy.json']+list(read(M4/'device-production-selection-0001/collected-results.json')['saved_sha256']),'demo')
gate('build-0035','device-development-restore-0011','org.packrag.product.PackImportConsentTest',['m3-import-consent.json'],timeout=300)
target=HERE/'device-execution.json';assert not target.exists();records=[]
for i,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('E1 device',i,'START',flush=True)
    with (HERE/f'device-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'device-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n')
    assert result.returncode==0,'E1 failed; stop later gates/milestones and preserve completed originals before any APK switch'
    print('E1 device',i,'PASS',flush=True)
target.write_text(json.dumps(dict(status='PASS_NEW_RETAINED_POLICY_RESTORED_ORIGINALS_NOT_E1_CLOSURE',commands=records),indent=2)+'\n')
