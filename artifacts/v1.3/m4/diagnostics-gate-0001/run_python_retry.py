"""Same full suite with normal host permissions and new output/temp locations.
Preserve run0016's sandbox-denied fixture and cleanup evidence unchanged.
"""
import json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
assert json.loads((HERE/'python-execution.json').read_text())['status']=='FAIL'
run=M4/'run-0017';run.mkdir(exist_ok=False);temporary=M4/'diagnostics-regression-temp-0002';temporary.mkdir(exist_ok=False)
env=dict(os.environ,TEMP=str(temporary),TMP=str(temporary));python=[sys.executable,'-X','utf8']
commands=[python+['-m','pytest','tests','product/tests','-p','no:cacheprovider','--basetemp',str(M4/'run-0017-temp'),
    '--junitxml',str(run/'combined-junit.xml'),'-q'],
    python+['-m','scripts.v13_result_manifest',str(run),'--command','Full E3 unchanged pytest tests product/tests; normal-host retry exact argv in diagnostics-gate-0001/run_python_retry.py']]
records=[];target=HERE/'python-retry-execution.json';assert not target.exists()
for i,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('E3 Python retry',i,'START',flush=True)
    with (HERE/f'python-retry-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'python-retry-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'Hold E3 progression; no assertions or product source are weakened'
    print('E3 Python retry',i,'PASS',flush=True)
target.write_text(json.dumps(dict(status='PASS_FULL_E3_PYTHON_HOST_PERMISSION_RETRY_NOT_COMPLETE_E3',commands=records,
    original_failed_run='run-0016',scope='Same suite/input source, new outputs/temp, normal host permissions; no ACL or test/product changes.'),indent=2)+'\n',encoding='utf-8')
