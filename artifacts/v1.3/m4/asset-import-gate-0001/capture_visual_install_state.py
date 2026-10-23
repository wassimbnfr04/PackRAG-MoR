"""Read-only exact installed APK proof and Android exit cause, no reinstall."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;ADB=ROOT/'vendor/platform-tools/adb.exe'
target=HERE/'visual-installed-state-0001.json';assert not target.exists()
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def adb(*args):
    result=subprocess.run([str(ADB),'-s','R3CT908DHHR',*args],capture_output=True,timeout=30)
    assert result.returncode==0
    return result.stdout
installed={}
for package,name in [('org.packrag.product','app-debug.apk'),('org.packrag.product.test','app-debug-androidTest.apk')]:
    raw=adb('shell','pm','path',package).decode().strip()
    assert re.fullmatch(r'package:/data/app/[A-Za-z0-9_./=+~-]+/base\.apk',raw),raw
    path=raw.removeprefix('package:')
    hashed=adb('shell','sha256sum',path).decode().strip()
    value=hashed.split()[0];assert re.fullmatch('[0-9a-f]{64}',value)
    expected=sha(ROOT/'artifacts/v1.3/m4/build-0075'/name);assert value==expected,(package,value,expected)
    installed[package]=dict(path=path,sha256=value,expected_sha256=expected,command_output=hashed)
exit_info=adb('shell','dumpsys','activity','exit-info','org.packrag.product')
path=HERE/'visual0002-application-exit-info.txt';assert not path.exists();path.write_bytes(exit_info)
assert b'reason=16 (PACKAGE UPDATED)' in exit_info and b'due to installPackageLI' in exit_info
target.write_text(json.dumps(dict(status='PASS_EXACT_INSTALLED_APK_IDENTITIES_NOT_VISUAL_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),installed=installed,exit_info_sha256=sha(path),scope='Android records19:33:05.792 PID9269 exit reason16 PACKAGE UPDATED, stop due to installPackageLI. visual0002 reached PREPARING but no control passed; package replacement terminated instrumentation, not a reported Java/native application crash. This proves update cause, not which installer session/human action. First timed-out installer may have remained pending; attribution to that session is inference. Next runner must verify installed APK bytes and avoid overlapping reinstallation; no security setting or upload choice automated.'),indent=2)+'\n',encoding='utf-8')
print('PASS_EXACT_INSTALLED_APK_IDENTITIES_PACKAGE_UPDATE_EXIT_OBSERVED')
