"""Short E2 compiled-policy gates while foreground availability is pending; restore development."""
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(HERE/'pair-preflight.json')['matched_variants']
assert read(HERE/'focused-device-execution.json')['status'].startswith('PASS_')
python=[sys.executable,'-X','utf8'];commands=[]
def add(build,run,classes,files,variant):
    commands.append(python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/build),'--run',str(M4/run),
        '--class-name',classes,'--result-file',files[0],'--timeout','900','--variant',variant])
    commands.append(python+['-m','scripts.v13_collect_phone_results','--run',str(M4/run),'--files',','.join(files)])
add('build-0040','device-source-details-policy-0001','org.packrag.product.SourceDetailsDeviceTest,org.packrag.product.SourceDetailsPolicyTest',
    ['m4-source-details-rows.json','m4-source-details-rejections.json','m4-source-details-policy.json'],'demo')
add('build-0039','device-development-restore-0012','org.packrag.product.PackImportConsentTest',['m3-import-consent.json'],'debug')
target=HERE/'focused-policy-execution.json';assert not target.exists();records=[]
for i,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('E2 focused policy',i,'START',flush=True)
    with (HERE/f'focused-policy-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'focused-policy-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'E2 focused policy failed; preserve originals and stop progression'
    print('E2 focused policy',i,'PASS',flush=True)
target.write_text(json.dumps(dict(status='PASS_NEW_E2_COMPILED_POLICY_ORIGINALS_AND_DEVELOPMENT_RESTORATION_NOT_FULL_POLICY_REGRESSION_OR_CLOSURE',commands=records),indent=2)+'\n',encoding='utf-8')
