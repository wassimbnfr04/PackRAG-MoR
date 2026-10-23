"""Identical walking module/input, normal host permissions, fresh immutable output."""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(HERE/'desktop-walking-execution.json')['status']=='FAIL'
failed=ROOT/'artifacts/v1.3/m4/existing-walking-smoke-0015';assert read(failed/'smoke-results.json')['cases']==[]
assert 'PermissionError' in (failed/'failure.txt').read_text(encoding='utf-8')
gate=read(ROOT/'artifacts/v1.3/m4/source-details-gate-0001/gate.json')
for n,v in gate['source_sha256'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v,n
target=HERE/'desktop-walking-retry-execution.json';assert not target.exists()
command=[sys.executable,'-X','utf8','-m','scripts.v13_existing_walking_smoke','--run',str(ROOT/'artifacts/v1.3/m4/existing-walking-smoke-0016')]
row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat())
target.write_text(json.dumps(dict(status='RUNNING',command=row),indent=2)+'\n',encoding='utf-8')
with (HERE/'desktop-walking-retry.stdout.txt').open('xb') as out,(HERE/'desktop-walking-retry.stderr.txt').open('xb') as err:
    result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat())
target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'PASS_NEW_ACTUAL_DESKTOP_WALKING_HOST_PERMISSION_RETRY_NOT_FULL_E3',command=row,
    scope='Same module/argv apart from new run path; normal host permissions, no ACL/input/test/runtime changes; original0015 failure preserved.'),indent=2)+'\n',encoding='utf-8')
assert result.returncode==0,'Hold progression and preserve failure'
print('E3 actual desktop walking retry PASS')
