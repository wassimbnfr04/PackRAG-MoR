"""E2 full regression and retained real desktop gates; immutable fresh outputs, fail closed."""
import json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
run=M4/'run-0015';run.mkdir(exist_ok=False);temporary=M4/'source-details-regression-temp-0001';temporary.mkdir(exist_ok=False)
env=dict(os.environ,TEMP=str(temporary),TMP=str(temporary));python=[sys.executable,'-X','utf8']
commands=[
    python+['-m','pytest','tests','product/tests','-p','no:cacheprovider','--basetemp',str(M4/'run-0015-temp'),'--junitxml',str(run/'combined-junit.xml'),'-q'],
    python+['-m','scripts.v13_result_manifest',str(run),'--command','Full E2 pytest tests product/tests; exact argv in source-details-gate-0001/run_regression.py'],
]
for module,name in [('v13_existing_walking_smoke','existing-walking-smoke-0014'),('v13_conflict_smoke','conflict-smoke-0008'),
    ('v13_relevance_smoke','relevance-smoke-0005'),('v13_representation_smoke','representation-smoke-0005'),
    ('v13_source_text_smoke','source-text-smoke-0003'),('v13_selection_smoke','selection-smoke-0003')]:
    commands.append(python+['-m','scripts.'+module,'--run',str(M4/name)])
records=[];target=HERE/'regression-execution.json';assert not target.exists()
for i,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('E2 regression',i,'START',flush=True)
    with (HERE/f'regression-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'regression-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'E2 validation failed; stop progression and preserve outputs'
    print('E2 regression',i,'PASS',flush=True)
target.write_text(json.dumps(dict(status='PASS_FULL_PYTHON_AND_ALL_RETAINED_DESKTOP_GATES_NOT_E2_CLOSURE',commands=records),indent=2)+'\n',encoding='utf-8')
