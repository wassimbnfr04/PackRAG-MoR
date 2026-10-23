import hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];BUILD=ROOT/'artifacts/v1.3/m4/build-0119';RUN=ROOT/'artifacts/v1.3/m4/emulator-native-quote-0002';RUN.mkdir(exist_ok=False)
ADB=ROOT/'vendor/platform-tools/adb.exe';SERIAL='emulator-5580'
record=dict(status='RUNNING_NOT_NATIVE_ACCEPTANCE',started_utc=datetime.now(timezone.utc).isoformat(),serial=SERIAL,commands=[])
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save():(RUN/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
def adb(*args,timeout=180,check=True,binary=False):
 r=subprocess.run([str(ADB),'-s',SERIAL,*args],capture_output=True,timeout=timeout)
 record['commands'].append(dict(args=list(args),returncode=r.returncode,stdout='Saved binary original' if binary else r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace')));save()
 if check:assert r.returncode==0
 return r
inputs=json.loads((BUILD/'source-at-build-start.json').read_text())['files']
try:
 assert len(inputs)==639
 for name,digest in inputs.items():assert sha(ROOT/name)==digest,name
 assert adb('shell','getprop','ro.kernel.qemu').stdout.strip()==b'1'
 record['apk_sha256']={p.name:sha(p) for p in [BUILD/'app-debug.apk',BUILD/'app-debug-androidTest.apk']}
 for name in record['apk_sha256']:assert b'Success' in adb('install','--no-streaming','-r',str(BUILD/name)).stdout
 for package,name in [('org.packrag.product','app-debug.apk'),('org.packrag.product.test','app-debug-androidTest.apk')]:
  path=adb('shell','pm','path',package).stdout.decode().strip().removeprefix('package:');assert path.startswith('/data/app/') and path.endswith('.apk')
  assert adb('shell','sha256sum',path).stdout.decode().split()[0]==record['apk_sha256'][name]
 result=adb('shell','am','instrument','-w','-r','-e','class','org.packrag.product.QuotedNativeRuntimeDeviceTest','org.packrag.product.test/androidx.test.runner.AndroidJUnitRunner',timeout=1800,check=False)
 (RUN/'instrumentation.txt').write_bytes(result.stdout);(RUN/'instrumentation.stderr.txt').write_bytes(result.stderr)
 raw=adb('exec-out','run-as','org.packrag.product','cat','files/m4-native-quoted-runtime-0001.json',check=False,binary=True)
 if raw.stdout.lstrip().startswith(b'{'):
  (RUN/'original-native-report.json').write_bytes(raw.stdout);report=json.loads(raw.stdout);record['observed_status']=report['status'];assert report['owner_sha256_before']==report['owner_sha256_after'];assert len(report['owner_sha256_before'])==5
 for name,digest in inputs.items():assert sha(ROOT/name)==digest,name
 assert result.returncode==0 and b'OK (1 test)' in result.stdout and b'FAILURES!!!' not in result.stdout
 assert record.get('observed_status')=='PASS'
 record.update(status='PASS_ACTUAL_EMULATOR_X86_NATIVE_QUOTE_CONTRACT_AND_WALKING_PATH_NOT_PHONE_OR_M4',phone_touched=False)
except BaseException as e:record.update(status='FAIL_NATIVE_QUOTE_GATE',error_type=type(e).__name__);raise
finally:record['updated_utc']=datetime.now(timezone.utc).isoformat();save()
print(record['status'],flush=True)
