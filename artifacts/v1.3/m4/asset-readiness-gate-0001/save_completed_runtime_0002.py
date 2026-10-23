"""Save a completed method original while the complete class is still running."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;run=ROOT/'artifacts/v1.3/m4/device-local-assets-0002'
target=HERE/'completed-runtime-0002.json';assert not target.exists()
name='m4-local-assets-runtime.json';argv=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/'+name]
out=subprocess.run(argv,capture_output=True,check=True,timeout=30);data=json.loads(out.stdout)
assert data['status']=='PASS' and len(data['cases'])==5 and all(row['passed'] is True for row in data['cases'])
assert data['actual_weight_inference'] is True and data['guards_unchanged'] is True
assert '74 °C' in data['answer'] and '[S1]' in data['answer'] and data['raw_reasoning_persisted'] is False
folder=run/'completed-method-originals';folder.mkdir(exist_ok=False);(folder/name).write_bytes(out.stdout)
record=dict(status='PASS_COMPLETED_RUNTIME_METHOD_ONLY_CLASS_STILL_RUNNING',recorded_utc=datetime.now(timezone.utc).isoformat(),
    argv=argv,returncode=out.returncode,stderr=out.stderr.decode('utf-8',errors='replace'),original_sha256=hashlib.sha256(out.stdout).hexdigest(),
    cases=5,emitted_tokens=data['emitted_tokens'],initialization_ms=data['initialization_ms'],session_wall_ms=data['session_wall_ms'],
    scope='One actual method completed including cold/warm/native recovery and owner guards. Two remaining methods, terminal class outcome and full originals remain required. These times are functional diagnostics, not hardware bottleneck acceptance.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
