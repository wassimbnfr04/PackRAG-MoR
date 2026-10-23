"""Pinned local SDK definition for observed numeric status; not a causal claim."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];run=ROOT/'artifacts/v1.3/m4/selection-running-resources-0001'
jar=ROOT/'vendor/android-sdk/platforms/android-37.0/android.jar';javap=ROOT/'vendor/java/jdk-17.0.20.1+1/bin/javap.exe'
command=[str(javap),'-constants','-classpath',str(jar),'android.os.PowerManager'];result=subprocess.run(command,capture_output=True,check=True)
lines=[v for v in result.stdout.splitlines() if b'THERMAL_STATUS_' in v];assert b'  public static final int THERMAL_STATUS_SEVERE = 3;' in lines
target=run/'sdk-thermal-constants.txt';assert not target.exists();target.write_bytes(b'\n'.join(lines)+b'\n')
with jar.open('rb') as stream:jar_sha=hashlib.file_digest(stream,'sha256').hexdigest()
target=run/'sdk-thermal-reference.json';assert not target.exists();target.write_text(json.dumps(dict(recorded_utc=datetime.now(timezone.utc).isoformat(),
    argv=command,returncode=result.returncode,jar_sha256=jar_sha,definition='PowerManager.THERMAL_STATUS_SEVERE=3',
    limits='The platform-reported severity label does not measure CPU clock, throttling magnitude, causality or a performance baseline'),indent=2)+'\n')
print('PINNED_SDK_STATUS_DEFINITION_RECORDED_NOT_CAUSAL_ATTRIBUTION')
