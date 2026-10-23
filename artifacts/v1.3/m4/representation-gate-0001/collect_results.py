"""Collect completed final structured phone evidence before changing APK variant."""
import argparse,hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];M4=ROOT/'artifacts/v1.3/m4'
parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);args=parser.parse_args()
run=M4/args.run;assert run.resolve().is_relative_to(M4)
manifest=json.loads((run/'instrumentation-manifest.json').read_text());assert manifest['status']=='PASS'
variant=manifest['variant'];assert variant in ('debug','demo')
prior=json.loads((M4/'relevance-gate-0001/gate.json').read_text())
old='device-relevance-0001' if variant=='debug' else 'device-production-relevance-0001'
names=prior['phone'][old]['saved_results']+['m4-representations.json','m4-representation-runtime.json']
assert len(names)==len(set(names))
raw=run/'original-adb';assert not raw.exists();raw.mkdir()
target=run/'collected-results.json';assert not target.exists();payloads={};saved={}
for name in names:
    assert Path(name).name==name and name.endswith('.json')
    result=subprocess.run([str(ROOT/'vendor/platform-tools/adb.exe'),'-s',manifest['serial'],'shell','run-as','org.packrag.product','cat','files/'+name],capture_output=True,timeout=30,check=True)
    parsed=json.loads(result.stdout);assert parsed['status']=='PASS',name
    if (run/name).exists():assert name=='m4-representations.json' and json.loads((run/name).read_text())==parsed
    payloads[name]=result.stdout;saved[name]=hashlib.sha256(result.stdout).hexdigest()
for name,payload in payloads.items():
    (raw/name).write_bytes(payload)
    if not (run/name).exists():
        with (run/name).open('xb') as stream:stream.write(payload)
target.write_text(json.dumps(dict(status='PASS',recorded_utc=datetime.now(timezone.utc).isoformat(),serial=manifest['serial'],apk_sha256=manifest['apk_sha256'],
    source='Final JSON after complete successful instrumentation; original-adb preserves every ADB byte; runner primary is formatted and parsed-equal.',saved_sha256=saved),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='PASS',run=args.run,saved=len(saved))))
