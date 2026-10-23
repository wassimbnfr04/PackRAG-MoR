"""Source-bound full D3 development gate; collect originals before any switch."""
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
prior=json.loads((M4/'device-representations-0002/instrumentation-manifest.json').read_text())
names=list(json.loads((M4/'device-representations-0002/collected-results.json').read_text())['saved_sha256'])+['m4-selection-tokenizer.json','m4-selection-runtime.json','m4-selection-guards.json']
assert len(names)==len(set(names))==30
commands=[
    [sys.executable,'-X','utf8','-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0028'),
        '--run',str(M4/'device-selection-full-0001'),'--class-name','org.packrag.product.SelectionDeviceTest,'+prior['class_name'],
        '--result-file','m4-selection-runtime.json','--timeout','4500'],
    [sys.executable,'-X','utf8','-m','scripts.v13_collect_phone_results','--run',str(M4/'device-selection-full-0001'),'--files',','.join(names)],
    [sys.executable,'-X','utf8',str(HERE/'verify_selection.py'),'--run',str(M4/'device-selection-full-0001'),'--target',str(HERE/'development-selection-parity.json')]
]
records=[]
for index,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('development stage',index,'START',flush=True)
    with (HERE/f'development-stage-{index}.stdout.txt').open('xb') as out,(HERE/f'development-stage-{index}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    (HERE/'development-execution.json').write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n')
    assert result.returncode==0,'Development gate failed; stop later milestones and preserve results'
    print('development stage',index,'PASS',flush=True)
(HERE/'development-execution.json').write_text(json.dumps(dict(status='PASS_FULL_DEVELOPMENT_NOT_POLICY_RESTORATION_OR_D3_CLOSURE',commands=records),indent=2)+'\n')
