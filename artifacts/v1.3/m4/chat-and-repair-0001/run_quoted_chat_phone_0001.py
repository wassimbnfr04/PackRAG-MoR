"""Prepare verified in-place install first; one separately authorized foreground smoke second."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];BUILD=ROOT/'artifacts/v1.3/m4/build-0120'
RUN=ROOT/'artifacts/v1.3/m4/phone-quoted-chat-0001';ADB=ROOT/'vendor/platform-tools/adb.exe';SERIAL='R3CT908DHHR'
parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--run',action='store_true');args=parser.parse_args()
assert args.prepare != args.run
if args.prepare:
 RUN.mkdir(exist_ok=False);record=dict(status='PREPARING_NO_UI_LAUNCH',started_utc=datetime.now(timezone.utc).isoformat(),serial=SERIAL,commands=[],phone_settings_changed=False)
else:
 record=json.loads((RUN/'execution.json').read_text());assert record['status']=='PREPARED_VERIFIED_APKS_NOT_UI_ACCEPTANCE'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save():(RUN/'execution.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
def adb(*values,check=True,binary=False,timeout=180):
 p=subprocess.run([str(ADB),'-s',SERIAL,*values],capture_output=True,timeout=timeout)
 record['commands'].append(dict(args=list(values),returncode=p.returncode,stdout='Saved original bytes' if binary else p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace')));save()
 if check:assert p.returncode==0,(values,p.stderr.decode(errors='replace'))
 return p
inputs=json.loads((BUILD/'source-at-build-start.json').read_text())['files']
def source_guard():
 assert len(inputs)==639
 for n,h in inputs.items():assert sha(ROOT/n)==h,n
def installed_guard():
 for package,name in [('org.packrag.product','app-debug.apk'),('org.packrag.product.test','app-debug-androidTest.apk')]:
  path=adb('shell','pm','path',package).stdout.decode().strip().removeprefix('package:')
  assert path.startswith('/data/app/') and path.endswith('.apk') and '\n' not in path
  assert adb('shell','sha256sum',path).stdout.decode().split()[0]==record['apk_sha256'][name]
try:
 source_guard();assert adb('shell','getprop','ro.product.model').stdout.strip()==b'SM-S908B'
 if args.prepare:
  capture=json.loads((Path(__file__).parent/'build-0120-capture.json').read_text())
  record['apk_sha256']={p.name:sha(p) for p in [BUILD/'app-debug.apk',BUILD/'app-debug-androidTest.apk']};assert record['apk_sha256']==capture['apk_sha256']
  for name in record['apk_sha256']:assert b'Success' in adb('install','--no-streaming','-r',str(BUILD/name)).stdout
  installed_guard();record['status']='PREPARED_VERIFIED_APKS_NOT_UI_ACCEPTANCE';save()
 else:
  installed_guard();record.update(status='RUNNING_SINGLE_FOREGROUND_SMOKE',untouched_window_minutes=18,authorization='Owner must explicitly approve fresh18-minute window before this --run invocation',instrumentation_started_utc=datetime.now(timezone.utc).isoformat());save()
  argv=[str(ADB),'-s',SERIAL,'shell','am','instrument','-w','-r','-e','class','org.packrag.product.QuotedChatRepairUiTest','org.packrag.product.test/androidx.test.runner.AndroidJUnitRunner']
  record['instrumentation_argv']=argv;save()
  with (RUN/'instrumentation.txt').open('wb') as out,(RUN/'instrumentation.stderr.txt').open('wb') as err:
   p=subprocess.Popen(argv,stdout=out,stderr=err);deadline=time.monotonic()+1800
   while p.poll() is None:
    if time.monotonic()>deadline:
     record.update(status='OBSERVER_EXPIRED_DEVICE_TEST_UNDISTURBED',device_test_stopped=False);save();raise RuntimeError('Observer expired; live test left undisturbed')
    time.sleep(2)
  record['instrumentation_returncode']=p.returncode
  originals=RUN/'original-adb';originals.mkdir()
  raw=adb('exec-out','run-as','org.packrag.product','cat','files/m4-quoted-chat-repair-0001.json',check=False,binary=True)
  if raw.stdout.lstrip().startswith(b'{'):
   (originals/'m4-quoted-chat-repair-0001.json').write_bytes(raw.stdout);d=json.loads(raw.stdout);record['observed_status']=d['status']
   names={'m4-quoted-guide-answer.png','m4-quoted-guide-source.png','m4-quoted-guide-diagnostic-tokens.png','m4-quoted-guide-diagnostic-policy.png'}
   for name,row in d.get('visual_png',{}).items():
    assert name in names;target=originals/name;target.write_bytes(adb('exec-out','run-as','org.packrag.product','cat','files/'+name,binary=True).stdout);assert sha(target)==row['sha256']
   record['original_sha256']={n.name:sha(n) for n in originals.iterdir()}
   assert len(d['owner_sha256_before'])==51
  source_guard();out=(RUN/'instrumentation.txt').read_bytes()
  assert p.returncode==0 and b'OK (1 test)' in out and b'FAILURES!!!' not in out,'Original failure retained'
  assert record.get('observed_status')=='PASS_EXECUTION_ORIGINAL_FINAL_AND_VISUAL_REVIEW_REQUIRED'
  record.update(status='PASS_EXECUTION_FINAL_AND_VISUAL_REVIEW_PENDING_NOT_M4',source_inputs_unchanged=639,owner_public_files_unchanged=51)
except BaseException as e:
 if record['status']!='OBSERVER_EXPIRED_DEVICE_TEST_UNDISTURBED':record['status']='FAIL_PREPARATION_OR_UI_GATE'
 record.update(error_type=type(e).__name__,error=str(e));raise
finally:record['updated_utc']=datetime.now(timezone.utc).isoformat();save()
print(record['status'],flush=True)
