"""Exact current APK emulator test; preserve originals including failed observations."""
import hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
BUILD=ROOT/'artifacts/v1.3/m4/build-0108';RUN=ROOT/'artifacts/v1.3/m4/emulator-chat-repair-0001'
RUN.mkdir(exist_ok=False);ADB=ROOT/'vendor/platform-tools/adb.exe';SERIAL='emulator-5580'
record=dict(status='RUNNING_NOT_NATIVE_OR_M4_ACCEPTANCE',started_utc=datetime.now(timezone.utc).isoformat(),serial=SERIAL,commands=[])
def save():(RUN/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def adb(*args,timeout=180,check=True,binary=False):
    r=subprocess.run([str(ADB),'-s',SERIAL,*args],capture_output=True,timeout=timeout)
    record['commands'].append(dict(args=list(args),returncode=r.returncode,stdout='Saved binary original' if binary else r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace')));save()
    if check:assert r.returncode==0
    return r
inputs=json.loads((BUILD/'source-at-build-start.json').read_text())['files']
try:
    assert len(inputs)==630
    for name,digest in inputs.items():assert sha(ROOT/name)==digest,name
    assert adb('shell','getprop','ro.kernel.qemu').stdout.strip()==b'1'
    assert adb('shell','settings','get','system','font_scale').stdout.strip()==b'1.0'
    assert sha(BUILD/'app-debug.apk')==sha(ROOT/'artifacts/v1.3/m4/build-0106/app-debug.apk')
    record['apk_sha256']={p.name:sha(p) for p in [BUILD/'app-debug.apk',BUILD/'app-debug-androidTest.apk']}
    for package,filename in [('org.packrag.product','app-debug.apk'),('org.packrag.product.test','app-debug-androidTest.apk')]:
        assert b'Success' in adb('install','--no-streaming','-r',str(BUILD/filename)).stdout
        installed=adb('shell','pm','path',package).stdout.decode().strip().removeprefix('package:')
        assert installed.startswith('/data/app/') and installed.endswith('/base.apk') and '\n' not in installed
        assert adb('shell','sha256sum',installed).stdout.decode().split()[0]==record['apk_sha256'][filename]
    result=adb('shell','am','instrument','-w','-r','-e','class','org.packrag.product.EmulatorChatRepairUiTest',
        'org.packrag.product.test/androidx.test.runner.AndroidJUnitRunner',timeout=2700,check=False)
    (RUN/'instrumentation.txt').write_bytes(result.stdout);(RUN/'instrumentation.stderr.txt').write_bytes(result.stderr)
    originals=RUN/'original-adb';originals.mkdir()
    raw=adb('exec-out','run-as','org.packrag.product','cat','files/m4-emulator-chat-repair.json',check=False,binary=True)
    if raw.returncode==0:
        (originals/'m4-emulator-chat-repair.json').write_bytes(raw.stdout)
        value=json.loads(raw.stdout);record['observed_status']=value['status']
        for name,declared in value.get('visual_png',{}).items():
            assert name in {'m4-emulator-repair-source.png','m4-emulator-repair-answer.png','m4-emulator-repair-diagnostics.png'}
            path=originals/name;path.write_bytes(adb('exec-out','run-as','org.packrag.product','cat','files/'+name,binary=True).stdout)
            assert sha(path)==declared['sha256']
        record['original_sha256']={p.name:sha(p) for p in originals.iterdir()}
    for name,digest in inputs.items():assert sha(ROOT/name)==digest,name
    assert result.returncode==0 and b'OK (1 test)' in result.stdout and b'FAILURES!!!' not in result.stdout
    assert record['observed_status']=='PASS_EXECUTION_ORIGINAL_FINAL_AND_PNG_REVIEW_REQUIRED'
    record.update(status='PASS_EXECUTION_FINAL_AND_PNG_REVIEW_PENDING_NOT_M4',phone_touched=False)
except BaseException as e:
    record.update(status='FAIL_NO_NATIVE_OR_M4_ACCEPTANCE',error_type=type(e).__name__);raise
finally:record['updated_utc']=datetime.now(timezone.utc).isoformat();save()
print(record['status'],flush=True)
