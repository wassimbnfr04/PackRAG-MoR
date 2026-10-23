"""After UI/visual acceptance: all retained/new development and compiled-policy methods, restore."""
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(HERE/'ui-execution-repaired.json')['status']=='PASS_FOUR_UI_METHODS_ORIGINALS_AND_SCREENSHOTS_SAVED_NOT_VISUAL_OR_E2_CLOSURE'
assert read(HERE/'visual-inspection-repaired.json')['status']=='PASS_AR_FR_CANONICAL_DISPLAY_NOT_SEMANTIC_REVIEW'
assert read(HERE/'regression-execution.json')['status']=='PASS_FULL_PYTHON_AND_ALL_RETAINED_DESKTOP_GATES_NOT_E2_CLOSURE'
python=[sys.executable,'-X','utf8'];commands=[]
def add(build,run,classes,files,variant='debug',timeout=4500):
    commands.append(python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/build),'--run',str(M4/run),
        '--class-name',classes,'--result-file',files[0],'--timeout',str(timeout),'--variant',variant])
    commands.append(python+['-m','scripts.v13_collect_phone_results','--run',str(M4/run),'--files',','.join(files)])
prior=M4/'device-query-regression-0001';classes=read(prior/'instrumentation-manifest.json')['class_name']
files=list(read(prior/'collected-results.json')['saved_sha256'])
add('build-0041','device-source-details-full-0001',
    'org.packrag.product.SourceDetailsDeviceTest,org.packrag.product.SourceDetailsViewModelTest,org.packrag.product.QueryControlsDeviceTest,'+classes,
    ['m4-source-details-rows.json','m4-source-details-rejections.json','m4-source-details-viewmodel.json','m4-ui-query-runtime.json','m4-ui-query-inputs.json']+files)
prior=M4/'device-query-policy-0001';classes=read(prior/'instrumentation-manifest.json')['class_name']
files=list(read(prior/'collected-results.json')['saved_sha256'])
add('build-0042','device-source-details-policy-full-0001',
    'org.packrag.product.SourceDetailsDeviceTest,org.packrag.product.SourceDetailsPolicyTest,'+classes,
    ['m4-source-details-rows.json','m4-source-details-rejections.json','m4-source-details-policy.json']+files,'demo')
add('build-0041','device-development-restore-0013','org.packrag.product.PackImportConsentTest',['m3-import-consent.json'],timeout=300)
target=HERE/'full-device-execution.json';assert not target.exists();records=[]
for i,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('E2 full phone',i,'START',flush=True)
    with (HERE/f'full-device-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'full-device-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'E2 full gate failed; preserve completed originals and stop progression'
    print('E2 full phone',i,'PASS',flush=True)
target.write_text(json.dumps(dict(status='PASS_ALL_DEVELOPMENT_POLICY_AND_RESTORATION_ORIGINALS_NOT_E2_CLOSURE',commands=records),indent=2)+'\n',encoding='utf-8')
