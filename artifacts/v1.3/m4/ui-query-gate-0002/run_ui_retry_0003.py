"""Authorized foreground window; source-bound development UI and original-byte collection."""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
inputs=json.loads((M4/'build-0035/source-at-build-start.json').read_text())['files']
for name,value in inputs.items():assert digest(ROOT/name)==value,name
python=[sys.executable,'-X','utf8'];run=M4/'device-ui-query-0003';records=[]
commands=[
    python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0035'),'--run',str(run),
        '--class-name','org.packrag.product.QueryControlsUiTest,org.packrag.product.PackManagementUiTest','--result-file','m4-ui-query-controls.json','--timeout','1200'],
    python+['-m','scripts.v13_collect_phone_results','--run',str(run),'--files','m4-ui-query-controls.json,m3-pack-management-ui.json']
]
target=HERE/'ui-execution-0003.json';assert not target.exists()
for i,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('E1 UI',i,'START',flush=True)
    with (HERE/f'ui0003-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'ui0003-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n')
    assert result.returncode==0,'UI failed; preserve originals before repair, do not start later milestones'
    print('E1 UI',i,'PASS',flush=True)
target.write_text(json.dumps(dict(status='PASS_TWO_FOREGROUND_METHODS_ORIGINALS_SAVED',commands=records),indent=2)+'\n')
