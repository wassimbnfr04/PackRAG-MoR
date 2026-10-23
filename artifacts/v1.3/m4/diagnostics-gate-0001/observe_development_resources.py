"""Asynchronous bounded functional resource sample, no tuning or benchmark claim."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
folder=HERE/'development-resource-observation-0001';folder.mkdir(exist_ok=False);records=[]
for name,args,filter_lines in [
    ('process',['shell','ps','-p','12346','-o','PID,STAT,TIME,NAME'],lambda line:True),
    ('thermal',['shell','dumpsys','thermalservice'],lambda line:'Thermal Status:' in line or ('Temperature{' in line and any(x in line for x in ['mName=AP,','mName=SKIN,','mName=skin,']))),
    ('memory',['shell','dumpsys','meminfo','12346'],lambda line:'TOTAL PSS:' in line or 'TOTAL RSS:' in line or 'TOTAL SWAP PSS:' in line or 'Native Heap' in line),
]:
    argv=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR']+args;started=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(argv,capture_output=True,check=True,timeout=30)
    text='\n'.join(line for line in result.stdout.decode('utf-8',errors='replace').splitlines() if filter_lines(line))+'\n'
    p=folder/(name+'.txt');p.write_text(text,encoding='utf-8')
    records.append(dict(argv=argv,returncode=result.returncode,started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),saved=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
target=folder/'observation.json';target.write_text(json.dumps(dict(status='READ_ONLY_ASYNCHRONOUS_FUNCTIONAL_RESOURCE_SAMPLE_NOT_BENCHMARK',commands=records,
    scope='Current development-test PID12346, separate sampling instants. Process TIME is printed verbatim, not wall elapsed or instantaneous CPU percentage. Memory is a reported sample, not a measured peak. Thermal status is reported raw; no causal diagnosis, thermal safety bypass, frequency/priority/radio/root/heap/affinity/RAM mutation.'),indent=2)+'\n',encoding='utf-8')
print('Bounded functional process/thermal/memory sample saved, no benchmark/causal claim')
