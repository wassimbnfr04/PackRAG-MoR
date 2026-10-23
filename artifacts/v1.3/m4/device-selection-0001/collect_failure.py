"""Preserve partial phone observations from a failed gate, never mark PASS."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
manifest=json.loads((HERE/'instrumentation-manifest.json').read_text());assert manifest['status']=='FAIL'
target=HERE/'original-adb-partial';target.mkdir(exist_ok=False);records=[]
names=['m4-selection-guards.json','m4-selection-guards-observed.json','m4-selection-runtime-progress.json','m4-selection-runtime-observed.json',
    'm4-selection-tokenizer-progress.json','m4-selection-tokenizer-observed.json']
for name in names:
    command=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s',manifest['serial'],'shell','run-as','org.packrag.product','cat','files/'+name]
    start=datetime.now(timezone.utc).isoformat();result=subprocess.run(command,capture_output=True,timeout=30)
    row=dict(argv=command,started_utc=start,ended_utc=datetime.now(timezone.utc).isoformat(),returncode=result.returncode)
    if result.returncode==0:
        parsed=json.loads(result.stdout);(target/name).write_bytes(result.stdout)
        row.update(observed_status=parsed.get('status'),sha256=hashlib.sha256(result.stdout).hexdigest())
    else:
        (target/(name+'.stderr.txt')).write_bytes(result.stderr);row['missing_or_error']=True
    records.append(row)
(HERE/'partial-collection.json').write_text(json.dumps(dict(status='FAILED_GATE_PARTIAL_OBSERVATIONS_NOT_ACCEPTANCE',apk_sha256=manifest['apk_sha256'],
    collector_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),commands=records),indent=2)+'\n')
print('FAILED_GATE_PARTIAL_OBSERVATIONS_SAVED')
