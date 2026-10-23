"""Read-only context for a long functional test, not benchmark or causality."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
run=M4/'selection-running-resources-0001';run.mkdir(exist_ok=False)
adb=ROOT/'vendor/platform-tools/adb.exe';base=[str(adb),'-s','R3CT908DHHR'];records=[]
for name,args in [('runner',['logcat','-d','-s','TestRunner:I']),('memory',['shell','dumpsys','meminfo','org.packrag.product']),('thermal',['shell','dumpsys','thermalservice']),('load',['shell','cat','/proc/loadavg'])]:
    command=base+args;start=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(command,capture_output=True,timeout=30)
    content=result.stdout
    if name=='runner':content=b'\n'.join(content.splitlines()[-8:])+b'\n'
    output=run/(name+'.stdout.txt');output.write_bytes(content);(run/(name+'.stderr.txt')).write_bytes(result.stderr)
    records.append(dict(argv=command,started_utc=start,finished_utc=datetime.now(timezone.utc).isoformat(),returncode=result.returncode,
        sha256=hashlib.sha256(content).hexdigest()))
(run/'observation.json').write_text(json.dumps(dict(status='READ_ONLY_FUNCTIONAL_TEST_CONTEXT_NOT_BENCHMARK',
    instrument_run='device-selection-reporter-0001',build='build-0030',commands=records,
    limits=['One asynchronous memory/thermal/load sample; not per-query peak or repeated measurement',
        'Load includes the device system and cannot attribute model time to hardware or software',
        'No runtime, phone RAM, governor, affinity, radios or app data settings changed',
        'Mobile data remains on; actual functional test continues uninterrupted']),indent=2)+'\n')
print('RESOURCE_CONTEXT_SAVED_NOT_PERFORMANCE_OR_BOTTLENECK_PROOF')
