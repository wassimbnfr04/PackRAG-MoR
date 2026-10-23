"""Normal-host-permission rerun after preserved sandbox failures; tests unchanged."""
import json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
run=M4/'run-0014';run.mkdir(exist_ok=False);temporary=M4/'ui-query-regression-temp-0002';temporary.mkdir(exist_ok=False)
env=dict(os.environ,TEMP=str(temporary),TMP=str(temporary));python=[sys.executable,'-X','utf8']
commands=[
    python+['-m','pytest','tests','product/tests','-p','no:cacheprovider','--basetemp',str(M4/'run-0014-temp'),'--junitxml',str(run/'combined-junit.xml'),'-q'],
    python+['-m','scripts.v13_result_manifest',str(run),'--command','Full pytest tests product/tests, normal host permissions after preserved sandbox failures; exact argv in ui-query-gate-0002'],
    python+['-m','scripts.v13_existing_walking_smoke','--run',str(M4/'existing-walking-smoke-0013')]
]
records=[];target=HERE/'regression-execution.json';assert not target.exists()
for i,command in enumerate(commands):
    record=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('E1 repaired regression',i,'START',flush=True)
    with (HERE/f'regression-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'regression-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=err)
    record.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(record)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n')
    assert result.returncode==0,'E1 gate failed; preserve original outputs and stop progression'
    print('E1 repaired regression',i,'PASS',flush=True)
target.write_text(json.dumps(dict(status='PASS_FULL_PYTHON_AND_RETAINED_DESKTOP_WALKING',commands=records),indent=2)+'\n')
