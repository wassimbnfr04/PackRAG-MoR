"""New E3 full Python regression, independently versioned and source-bound."""
import json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
run=M4/'run-0016';run.mkdir(exist_ok=False);temporary=M4/'diagnostics-regression-temp-0001';temporary.mkdir(exist_ok=False)
env=dict(os.environ,TEMP=str(temporary),TMP=str(temporary));python=[sys.executable,'-X','utf8']
commands=[python+['-m','pytest','tests','product/tests','-p','no:cacheprovider','--basetemp',str(M4/'run-0016-temp'),
    '--junitxml',str(run/'combined-junit.xml'),'-q'],
    python+['-m','scripts.v13_result_manifest',str(run),'--command','Full E3 pytest tests product/tests; exact argv in diagnostics-gate-0001/run_python.py']]
records=[];target=HERE/'python-execution.json';assert not target.exists()
for i,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('E3 Python',i,'START',flush=True)
    with (HERE/f'python-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'python-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'Hold E3 progression and preserve regression failure'
    print('E3 Python',i,'PASS',flush=True)
target.write_text(json.dumps(dict(status='PASS_FULL_E3_PYTHON_NOT_ANDROID_OR_COMPLETE_E3',commands=records),indent=2)+'\n',encoding='utf-8')
