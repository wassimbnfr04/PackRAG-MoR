"""One read-only process/thermal observation during the policy gate."""
import json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;ADB=ROOT/'vendor/platform-tools/adb.exe'
target=HERE/'observation.json';assert not target.exists();records=[]
def call(name,args):
    started=datetime.now(timezone.utc).isoformat();command=[str(ADB),'-s','R3CT908DHHR',*args]
    result=subprocess.run(command,capture_output=True,timeout=30);(HERE/(name+'-stdout.txt')).write_bytes(result.stdout);(HERE/(name+'-stderr.txt')).write_bytes(result.stderr)
    records.append(dict(name=name,argv=command,returncode=result.returncode,started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat()))
    return result
result=call('pid',['shell','pidof','org.packrag.product']);pids=result.stdout.decode().split();assert result.returncode==0 and len(pids)==1 and pids[0].isdigit();pid=pids[0]
for name,file in [('status','status'),('cgroup','cgroup'),('sched','sched')]:call(name,['shell','run-as','org.packrag.product','cat','/proc/'+pid+'/'+file])
call('thermal',['shell','dumpsys','thermalservice'])
call('activity',['shell','dumpsys','activity','processes','org.packrag.product'])
call('test-progress',['logcat','-d','-s','TestRunner:I'])
target.write_text(json.dumps(dict(status='ONE_READ_ONLY_OBSERVATION_NOT_PER_QUERY_PEAK_OR_CAUSAL_BOTTLENECK_PROOF',during_run='device-production-representations-0002',pid=pid,commands=records,limits=['Different files sampled at different instants; not synchronized per-query telemetry','No controlled alternative hardware/software trial; does not identify cause of timing differences','No scheduler/radio/affinity/governor/root/thermal change or test interruption','Permission-denied outputs, if any, remain explicit; no permission bypass']),indent=2)+'\n')
print(json.dumps(dict(status='SAVED_READ_ONLY_OBSERVATION',pid=pid,returncodes={r['name']:r['returncode'] for r in records})))
