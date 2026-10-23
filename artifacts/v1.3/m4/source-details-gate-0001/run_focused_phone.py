"""New background E2 registry/source/ViewModel gates; collect originals before any switch."""
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
assert json.loads((HERE/'debug-preflight.json').read_text())['status'].startswith('PASS_')
run=M4/'device-source-details-0001';python=[sys.executable,'-X','utf8']
commands=[python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0039'),'--run',str(run),
    '--class-name','org.packrag.product.SourceDetailsDeviceTest,org.packrag.product.SourceDetailsViewModelTest',
    '--result-file','m4-source-details-rows.json','--timeout','1800'],
    python+['-m','scripts.v13_collect_phone_results','--run',str(run),'--files','m4-source-details-rows.json,m4-source-details-rejections.json,m4-source-details-viewmodel.json']]
target=HERE/'focused-device-execution.json';assert not target.exists();records=[]
for i,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('E2 focused phone',i,'START',flush=True)
    with (HERE/f'focused-device-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'focused-device-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'E2 focused gate failed; stop progression, preserve completed originals before APK change'
    print('E2 focused phone',i,'PASS',flush=True)
target.write_text(json.dumps(dict(status='PASS_NEW_E2_BACKGROUND_METHODS_ORIGINALS_SAVED_NOT_E2_CLOSURE',commands=records),indent=2)+'\n',encoding='utf-8')
