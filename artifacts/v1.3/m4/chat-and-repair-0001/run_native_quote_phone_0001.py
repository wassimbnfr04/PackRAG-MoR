"""One existing-build actual ARM native gate; never stop a live device test on observer expiry."""
import hashlib,json,subprocess,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4]
BUILD=ROOT/'artifacts/v1.3/m4/build-0119'
RUN=ROOT/'artifacts/v1.3/m4/phone-native-quote-0001'
RUN.mkdir(exist_ok=False)
ADB=ROOT/'vendor/platform-tools/adb.exe';SERIAL='R3CT908DHHR'
record=dict(status='RUNNING_NOT_ACCEPTANCE',started_utc=datetime.now(timezone.utc).isoformat(),serial=SERIAL,commands=[],radios_or_settings_changed=False)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save():(RUN/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
def adb(*args,timeout=180,check=True,binary=False):
 r=subprocess.run([str(ADB),'-s',SERIAL,*args],capture_output=True,timeout=timeout)
 record['commands'].append(dict(args=list(args),returncode=r.returncode,stdout='Saved original bytes' if binary else r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace')));save()
 if check:assert r.returncode==0,(args,r.stderr.decode(errors='replace'))
 return r
inputs=json.loads((BUILD/'source-at-build-start.json').read_text())['files']
try:
 assert len(inputs)==639
 for name,digest in inputs.items():assert sha(ROOT/name)==digest,name
 assert adb('shell','getprop','ro.product.model').stdout.strip()==b'SM-S908B'
 assert adb('shell','getprop','ro.product.cpu.abi').stdout.strip()==b'arm64-v8a'
 assert adb('shell','getprop','ro.kernel.qemu').stdout.strip()!=b'1'
 capture=json.loads((Path(__file__).parent/'build-0119-capture.json').read_text())
 record['apk_sha256']={p.name:sha(p) for p in [BUILD/'app-debug.apk',BUILD/'app-debug-androidTest.apk']}
 assert record['apk_sha256']==capture['apk_sha256']
 for name in record['apk_sha256']:
  assert b'Success' in adb('install','--no-streaming','-r',str(BUILD/name)).stdout
 for package,name in [('org.packrag.product','app-debug.apk'),('org.packrag.product.test','app-debug-androidTest.apk')]:
  path=adb('shell','pm','path',package).stdout.decode().strip().removeprefix('package:')
  assert path.startswith('/data/app/') and path.endswith('.apk')
  assert adb('shell','sha256sum',path).stdout.decode().split()[0]==record['apk_sha256'][name]
 record['instrumentation_started_utc']=datetime.now(timezone.utc).isoformat();save()
 argv=[str(ADB),'-s',SERIAL,'shell','am','instrument','-w','-r','-e','class','org.packrag.product.QuotedNativeRuntimeDeviceTest','org.packrag.product.test/androidx.test.runner.AndroidJUnitRunner']
 record['instrumentation_argv']=argv;save()
 with (RUN/'instrumentation.txt').open('wb') as out,(RUN/'instrumentation.stderr.txt').open('wb') as err:
  proc=subprocess.Popen(argv,stdout=out,stderr=err)
  record['observer_pid']=proc.pid;save()
  deadline=time.monotonic()+1800
  while proc.poll() is None:
   if time.monotonic()>deadline:
    record.update(status='OBSERVER_EXPIRED_DEVICE_TEST_UNDISTURBED',device_test_stopped=False);save()
    print(record['status'],flush=True);raise RuntimeError('Observer expiry; adb/device instrumentation intentionally left undisturbed')
   time.sleep(2)
 record['instrumentation_returncode']=proc.returncode
 output=(RUN/'instrumentation.txt').read_bytes()
 assert proc.returncode==0 and b'OK (1 test)' in output and b'FAILURES!!!' not in output, 'Original instrumentation failure retained'
 raw=adb('exec-out','run-as','org.packrag.product','cat','files/m4-native-quoted-runtime-0001.json',binary=True)
 (RUN/'original-native-report.json').write_bytes(raw.stdout);report=json.loads(raw.stdout)
 assert report['status']=='PASS' and report['environment']=='PHYSICAL_ARM64'
 assert report['native_abi']=='arm64-v8a'
 assert report['owner_sha256_before']==report['owner_sha256_after']
 assert len(report['owner_sha256_before'])==51
 for name,digest in inputs.items():assert sha(ROOT/name)==digest,name
 record.update(status='PASS_ACTUAL_PHONE_NATIVE_QUOTE_CONTRACT_AND_WALKING_PATH_NOT_UI_OR_M4',observed_report_sha256=sha(RUN/'original-native-report.json'),android_inputs_unchanged=639,owner_public_files_unchanged=51)
except BaseException as e:
 if record['status']!='OBSERVER_EXPIRED_DEVICE_TEST_UNDISTURBED':record.update(status='FAIL_NATIVE_PHONE_GATE')
 record.update(error_type=type(e).__name__,error=str(e));raise
finally:record['updated_utc']=datetime.now(timezone.utc).isoformat();save()
print(record['status'],flush=True)
