"""Stop at any failed iteration; no UI or later milestone work is dispatched here."""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
target=HERE/'hardening-walking-sequence-0001.json';assert not target.exists()
steps=[['run_hardening.py','--build','build-0062','--run','device-local-asset-import-faults-0001'],
       ['run_walking.py','--build','build-0062','--run','device-local-asset-import-walking-0003']]
record=dict(status='RUNNING',started_utc=datetime.now(timezone.utc).isoformat(),commands=[])
try:
    for i,step in enumerate(steps):
        argv=[sys.executable,'-X','utf8',str(HERE/step[0]),*step[1:]];start=datetime.now(timezone.utc).isoformat()
        with (HERE/f'hardening-walking-sequence-0001-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'hardening-walking-sequence-0001-stage-{i}.stderr.txt').open('xb') as err:
            print('F2 hardening/native sequence stage',i,'START',flush=True);result=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=err)
        record['commands'].append(dict(argv=argv,started_utc=start,finished_utc=datetime.now(timezone.utc).isoformat(),returncode=result.returncode))
        target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');assert result.returncode==0,'Hold progression; save passing originals and repair before later F2 work'
        print('F2 hardening/native sequence stage',i,'PASS',flush=True)
    record.update(status='PASS_F2_HARDENING_AND_NATIVE_API_REGRESSION_NOT_FULL_F2',finished_utc=datetime.now(timezone.utc).isoformat())
except Exception as failure:
    record.update(status='FAIL',finished_utc=datetime.now(timezone.utc).isoformat(),failure_type=type(failure).__name__,failure_message=str(failure));raise
finally:target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
