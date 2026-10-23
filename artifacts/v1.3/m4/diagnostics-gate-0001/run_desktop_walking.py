"""New actual retained walking path, no content authoring or historic output edits."""
import json,subprocess,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
gate=read(ROOT/'artifacts/v1.3/m4/source-details-gate-0001/gate.json')
for n,v in gate['source_sha256'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v,n
target=HERE/'desktop-walking-execution.json';assert not target.exists()
command=[sys.executable,'-X','utf8','-m','scripts.v13_existing_walking_smoke','--run',str(ROOT/'artifacts/v1.3/m4/existing-walking-smoke-0015')]
row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat())
target.write_text(json.dumps(dict(status='RUNNING',command=row),indent=2)+'\n',encoding='utf-8')
with (HERE/'desktop-walking.stdout.txt').open('xb') as out,(HERE/'desktop-walking.stderr.txt').open('xb') as err:
    result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat())
target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'PASS_NEW_ACTUAL_DESKTOP_WALKING_NOT_FULL_E3',command=row),indent=2)+'\n',encoding='utf-8')
assert result.returncode==0,'Hold progression and preserve failure'
print('E3 actual desktop walking PASS')
