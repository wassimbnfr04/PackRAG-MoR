"""Bind existing accepted results to exact current source and unchanged historical evidence."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];RUN=ROOT/'artifacts/v1.3/m4/chat-repair-final-gate-0001'
RUN.mkdir(exist_ok=False)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
hist=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files']
assert len(hist)==587
for n,h in hist.items():
 assert '.private' not in Path(n).parts and 'private-key' not in n.lower()
 assert sha(ROOT/n)==h,n
python=ROOT/'artifacts/v1.3/m4/quote-complete-python-regression-0001'
pyinputs=read(python/'inputs.json');assert len(pyinputs)==211
for n,h in pyinputs.items():assert sha(ROOT/n)==h,n
py=read(python/'result.json');assert py['status']=='PASS' and py['inputs_unchanged']
assert py['suites'][0]['tests']=='1054' and all(py['suites'][0][n]=='0' for n in ['errors','failures','skipped'])
android=read(ROOT/'artifacts/v1.3/m4/build-0122/source-at-build-start.json')['files'];assert len(android)==640
for n,h in android.items():assert sha(ROOT/n)==h,n
builds={}
for b,count in [('build-0120',639),('build-0121',639),('build-0122',640)]:
 capture=read(Path(__file__).parent/(b+'-capture.json'));assert capture['android_inputs']==count
 assert capture['status']=='PASS_LOCAL_F3F4_BUILD_HOST_APK_CONTRACTS_NOT_DEVICE_OR_INCREMENT_ACCEPTANCE'
 assert capture['host_xml_totals']==dict(tests=99,failures=0,errors=0,skipped=0)
 for name,h in capture['apk_sha256'].items():assert sha(ROOT/'artifacts/v1.3/m4'/b/name)==h
 builds[b]=dict(capture_sha256=sha(Path(__file__).parent/(b+'-capture.json')),apk_sha256=capture['apk_sha256'],native_pins=capture['actual_native_pins'],host_totals=capture['host_xml_totals'])
native=ROOT/'artifacts/v1.3/m4/phone-native-quote-0001';ui=ROOT/'artifacts/v1.3/m4/phone-quoted-chat-0001';policy=ROOT/'artifacts/v1.3/m4/phone-quoted-policy-0001'
assert read(native/'execution.json')['status']=='PASS_ACTUAL_PHONE_NATIVE_QUOTE_CONTRACT_AND_WALKING_PATH_NOT_UI_OR_M4'
assert read(native/'final-semantic-review-0001.json')['status']=='PASS_COMPLETE_CANONICAL_SINGLE_UNIT_GUIDE_AND_NEGATIVE_CONTROL'
assert read(ui/'execution.json')['status']=='PASS_EXECUTION_FINAL_AND_VISUAL_REVIEW_PENDING_NOT_M4'
assert read(ui/'visual-review-0001.json')['status']=='PASS_ORIGINAL_SCOPED_VISUAL_AND_FINAL_REVIEW_NOT_M4'
assert read(policy/'execution.json')['status']=='PASS_POLICY_AND_VERIFIED_DEBUG_RESTORATION_NOT_M4'
assert read(policy/'post-debug-restoration-owner-guard-0001.json')['status']=='PASS51_ORIGINAL_PUBLIC_FILES_AFTER_VERIFIED_DEBUG_RESTORATION'
evidence={}
for parent,names in [(python,['inputs.json','result.json','pytest.xml','stdout.txt','stderr.txt']),
 (native,['execution.json','instrumentation.txt','original-native-report.json','final-semantic-review-0001.json']),
 (ui,['execution.json','instrumentation.txt','visual-review-0001.json','original-adb/m4-quoted-chat-repair-0001.json',*[f'original-adb/m4-quoted-guide-{n}.png' for n in ['answer','source','diagnostic-tokens','diagnostic-policy']]]),
 (policy,['execution.json','instrumentation.txt','original-policy-report.json','post-debug-restoration-owner-guard-0001.json'])]:
 for n in names:
  p=parent/n;evidence[p.relative_to(ROOT).as_posix()]=sha(p)
record=dict(status='PASS_CURRENT_RUNTIME_PRIMARY_UI_COMPILED_POLICY_SOURCE_HISTORICAL_OWNER_AUDIT_CHECKPOINT_PENDING',utc=datetime.now(timezone.utc).isoformat(),
 historical_files_unchanged=587,python_inputs_unchanged=211,python_tests=1054,android_current_inputs_unchanged=640,builds=builds,evidence_sha256=evidence,
 current_android_source_sha256=android,current_python_source_sha256=pyinputs,
 scopes=['Actual ARM canonical guide/negative/cap/cancel/token-template-grammar parity/deactivation and51 owner hashes; no raw reasoning persisted.',
 'Current primary factory guide/source/visible metrics/profile/earlier source/recreation/Newchat/deactivation and original scoped visual review.',
 'Matched instrumentable demo compiled nondevelopment admission/no-INTERNET/no debug-routing bypass, exact historical report restoration/51owner and verified0120debug reinstall.',
 '1054 Python regression/99host per matched build and exact current/dated source/APK/native/config manifests. Unchanged components require their recorded dated scope, not whole-APK equivalence.'],
 limits=['KnownG0-C02 missing6A stays countedFAIL;24/25 meets unchanged9/4/4/4 promotion thresholds, not perfect accuracy.',
 'Repeated inspected development comparison, no heldout/general multi-unit completeness or manufacturer/source-truth proof.',
 'Functional guide latency559302.601875ms in native test; current whole UI class341.679s is a different scope, not a controlled speed comparison.',
 'SampledPSS not peak, first emission may be reasoning, remaining includes terminal; no controlled hardware/software/thermal conclusion.',
 'Original optional emulator observer timed out; actual test remains undisturbed and tied to0119 source capsule/APKs; no emulator pass inferred.',
 'F4 documentation/traceability and exact public checkpoint remain beforeM4 closure; M5–M8 and final owner-pack content/gold/calibration remain separate.'])
(RUN/'audit.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(record['status'],flush=True)
