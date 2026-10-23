"""Sequential retained real-model gates; versioned outputs, stop on failure."""
import json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
temp=HERE/'runner-temp';temp.mkdir(exist_ok=False);env=dict(os.environ,TEMP=str(temp),TMP=str(temp));records=[]
for module,name in [('v13_conflict_smoke','conflict-smoke-0007'),('v13_relevance_smoke','relevance-smoke-0004'),('v13_representation_smoke','representation-smoke-0004'),('v13_source_text_smoke','source-text-smoke-0002')]:
    run=ROOT/'artifacts/v1.3/m4'/name;assert not run.exists()
    command=[sys.executable,'-X','utf8','-m','scripts.'+module,'--run',str(run)]
    record=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print(name,'START',flush=True)
    with (HERE/(name+'-runner.txt')).open('xb') as output:result=subprocess.run(command,cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT)
    record.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(record)
    (HERE/'desktop-runner-record.json').write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n')
    assert result.returncode==0,name+' failed: stop progression and inspect retained log'
    print(name,'PASS',flush=True)
(HERE/'desktop-runner-record.json').write_text(json.dumps(dict(status='PASS',commands=records),indent=2)+'\n')
