"""One background compiled-policy regression; preserve old report and restore verified debug install."""
import hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];BUILD=ROOT/'artifacts/v1.3/m4/build-0122';DEBUG=ROOT/'artifacts/v1.3/m4/build-0120'
RUN=ROOT/'artifacts/v1.3/m4/phone-quoted-policy-0001';ADB=ROOT/'vendor/platform-tools/adb.exe';SERIAL='R3CT908DHHR'
ui=ROOT/'artifacts/v1.3/m4/phone-quoted-chat-0001'
assert json.loads((ui/'execution.json').read_text())['status']=='PASS_EXECUTION_FINAL_AND_VISUAL_REVIEW_PENDING_NOT_M4'
assert json.loads((ui/'visual-review-0001.json').read_text())['status']=='PASS_ORIGINAL_SCOPED_VISUAL_AND_FINAL_REVIEW_NOT_M4'
RUN.mkdir(exist_ok=False);record=dict(status='PREPARING_BACKGROUND_POLICY',utc=datetime.now(timezone.utc).isoformat(),commands=[],phone_settings_changed=False)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save():(RUN/'execution.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
def adb(*args,check=True,binary=False,timeout=180):
 p=subprocess.run([str(ADB),'-s',SERIAL,*args],capture_output=True,timeout=timeout)
 record['commands'].append(dict(args=list(args),returncode=p.returncode,stdout='Saved original bytes' if binary else p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace')));save()
 if check:assert p.returncode==0,(args,p.stderr.decode(errors='replace'))
 return p
def install(build,variant):
 captured=json.loads((Path(__file__).parent/(build.name+'-capture.json')).read_text())['apk_sha256']
 for package,name in [('org.packrag.product',f'app-{variant}.apk'),('org.packrag.product.test',f'app-{variant}-androidTest.apk')]:
  assert sha(build/name)==captured[name]
  assert b'Success' in adb('install','--no-streaming','-r',str(build/name)).stdout
  path=adb('shell','pm','path',package).stdout.decode().strip().removeprefix('package:');assert path.startswith('/data/app/') and path.endswith('.apk')
  assert adb('shell','sha256sum',path).stdout.decode().split()[0]==captured[name]
inputs=json.loads((BUILD/'source-at-build-start.json').read_text())['files']
try:
 assert len(inputs)==640
 for n,h in inputs.items():assert sha(ROOT/n)==h,n
 install(BUILD,'demo');record['status']='RUNNING_BACKGROUND_COMPILED_POLICY';save()
 p=adb('shell','am','instrument','-w','-r','-e','class','org.packrag.product.QuotedProductionPolicyDeviceTest','org.packrag.product.test/androidx.test.runner.AndroidJUnitRunner',timeout=600,check=False)
 (RUN/'instrumentation.txt').write_bytes(p.stdout);(RUN/'instrumentation.stderr.txt').write_bytes(p.stderr)
 assert p.returncode==0 and b'OK (1 test)' in p.stdout and b'FAILURES!!!' not in p.stdout,'Original failure retained'
 raw=adb('exec-out','run-as','org.packrag.product','cat','files/m4-quoted-production-policy-0001.json',binary=True)
 (RUN/'original-policy-report.json').write_bytes(raw.stdout);d=json.loads(raw.stdout)
 assert d['status']=='PASS' and d['original_test_report_restored'] is True and d['actual_model_inference'] is False
 assert d['owner_sha256_before']==d['owner_sha256_after'] and len(d['owner_sha256_before'])==51
 assert d['no_internet_permission'] and not d['development_mode'] and d['variant']=='demo'
 assert d['current_generation_config_sha256']=='dae71e602caa7f10e9030f4a19e21b44d513067ebccbc9ccee600b996965225d'
 for n,h in inputs.items():assert sha(ROOT/n)==h,n
 record.update(policy_status='PASS_CURRENT_COMPILED_NONDEVELOPMENT_POLICY_NOT_FINAL_RELEASE',owner_public_files_unchanged=51,current_source_inputs_unchanged=640)
 install(DEBUG,'debug');record.update(status='PASS_POLICY_AND_VERIFIED_DEBUG_RESTORATION_NOT_M4',restored_debug_build='build-0120');save()
except BaseException as e:record.update(status='FAIL_POLICY_OR_RESTORATION',error_type=type(e).__name__,error=str(e));raise
finally:record['updated_utc']=datetime.now(timezone.utc).isoformat();save()
print(record['status'],flush=True)
