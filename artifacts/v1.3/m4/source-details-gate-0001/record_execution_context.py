"""One read-only process-context sample during functional regression; not a benchmark."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];M4=ROOT/'artifacts/v1.3/m4'
target=M4/'source-details-execution-context-0001';assert not target.exists()
adb=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR']
result=subprocess.run(adb+['shell','pidof','org.packrag.product'],capture_output=True,check=True,timeout=30)
pid=result.stdout.decode().strip();assert pid.isdecimal()
payloads={};commands=[]
for name,leaf in [('cgroup.txt','cgroup'),('status.txt','status')]:
    command=adb+['exec-out','run-as','org.packrag.product','cat',f'/proc/{pid}/{leaf}']
    start=datetime.now(timezone.utc).isoformat();result=subprocess.run(command,capture_output=True,timeout=30)
    commands.append(dict(argv=command,started_utc=start,finished_utc=datetime.now(timezone.utc).isoformat(),
        returncode=result.returncode,stderr_utf8=result.stderr.decode('utf-8',errors='replace')))
    assert result.returncode==0
    payloads[name]=result.stdout
target.mkdir()
for name,value in payloads.items():(target/name).write_bytes(value)
text=payloads['status.txt'].decode('utf-8');keys={'State','Threads','Cpus_allowed_list','VmRSS','VmSwap'}
selected={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in text.splitlines() if ':' in line and line.split(':',1)[0] in keys}
(target/'record.json').write_text(json.dumps(dict(status='READ_ONLY_PROCESS_CONTEXT_SAMPLE_NOT_PERFORMANCE_OR_CAUSAL_BOTTLENECK_ACCEPTANCE',
    recorded_utc=datetime.now(timezone.utc).isoformat(),pid=int(pid),pending_run='device-source-details-full-0001',commands=commands,
    observed_status=selected,raw_sha256={name:hashlib.sha256(value).hexdigest() for name,value in payloads.items()},
    limits=['Two sequential reads, not simultaneous process/thermal/latency sampling.',
        'Main-process allowed CPU list is not per-worker placement, frequency, utilization or proof that every permitted core was used.',
        'One RSS/swap snapshot is not peak/PSS memory and may be between model/test transitions.',
        'No radio, affinity, scheduler, governor, privileges, heap or RAM setting changed; functional tests continue.']),indent=2)+'\n',encoding='utf-8')
print('Saved read-only process context; no hardware/software bottleneck or peak-memory claim')
