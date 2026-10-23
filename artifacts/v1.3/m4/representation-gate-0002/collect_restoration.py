"""Save original restored-consent JSON after its completed successful runner."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];RUN=ROOT/'artifacts/v1.3/m4/device-development-restore-0009'
manifest=json.loads((RUN/'instrumentation-manifest.json').read_text());assert manifest['status']=='PASS' and manifest['variant']=='debug'
name='m3-import-consent.json';result=subprocess.run([str(ROOT/'vendor/platform-tools/adb.exe'),'-s',manifest['serial'],'shell','run-as','org.packrag.product','cat','files/'+name],capture_output=True,check=True,timeout=30)
value=json.loads(result.stdout);assert value['status']=='PASS' and value==json.loads((RUN/name).read_text())
raw=RUN/'original-adb';assert not raw.exists();raw.mkdir();(raw/name).write_bytes(result.stdout)
target=RUN/'collected-results.json';assert not target.exists();target.write_text(json.dumps(dict(status='PASS',recorded_utc=datetime.now(timezone.utc).isoformat(),saved_sha256={name:hashlib.sha256(result.stdout).hexdigest()},source='Original ADB bytes; runner primary is formatted and parsed-equal',apk_sha256=manifest['apk_sha256']),indent=2)+'\n')
print('PASS restored-consent original bytes saved')
