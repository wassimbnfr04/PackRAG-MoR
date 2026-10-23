"""Preserve completed first method while full37 continues; never claim full PASS."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
folder=HERE/'development-completed-runtime-0001';folder.mkdir(exist_ok=False);commands=[]
def adb(args):
    argv=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR']+args
    result=subprocess.run(argv,capture_output=True,check=True,timeout=30);commands.append(dict(argv=argv,returncode=result.returncode));return result.stdout
method='actualColdWarmAndNoPackDiagnosticsKeepOwnedContextAfterReaderClose'
logs=adb(['logcat','-d','-s','TestRunner:I']).decode('utf-8',errors='replace');logs='\n'.join(line for line in logs.splitlines() if re.search(r'\s12346\s',line))+'\n'
assert 'run started: 37 tests' in logs and 'finished: '+method in logs and 'failed: '+method not in logs
(folder/'test-runner.txt').write_text(logs,encoding='utf-8')
name='m4-diagnostic-runtime.json';data=adb(['shell','run-as','org.packrag.product','cat','files/'+name]);value=json.loads(data)
assert value['status']=='PASS' and len(value['cases'])==8 and all(r['passed'] for r in value['cases']) and value['actual_weight_inference'] and value['raw_reasoning_persisted'] is False
for phase in ['cold','warm']:
    row=value[phase];assert row['outcome']=='ANSWER_ACCEPTED' and '74 °C' in row['answer'] and '[S1]' in row['answer'] and '</think>' not in row['answer']
before=json.loads((M4/'device-diagnostics-0003/m4-diagnostic-runtime.json').read_text(encoding='utf-8'))['owner_registry_and_model_sha256']
assert value['owner_registry_and_model_sha256']==before
raw=folder/'original-adb';raw.mkdir();(raw/name).write_bytes(data)
test='product/android/app/src/androidTest/java/org/packrag/product/DiagnosticRuntimeDeviceTest.kt'
inputs=json.loads((M4/'build-0052/source-at-build-start.json').read_text(encoding='utf-8'))['files'];assert hashlib.sha256((ROOT/test).read_bytes()).hexdigest()==inputs[test]
(folder/'progress.json').write_text(json.dumps(dict(status='COMPLETED_DEVELOPMENT_RUNTIME_METHOD_ORIGINAL_SAVED_FULL37_STILL_RUNNING',recorded_utc=datetime.now(timezone.utc).isoformat(),
    build='build-0052',actual_main_test_pid=12346,method=method,selected_test_source=test,selected_test_sha256=inputs[test],
    original_sha256=hashlib.sha256(data).hexdigest(),commands=commands,
    scope='One fresh completed method/eight controls in full development run. Remaining36 methods/final JUnit/full originals/parity/closure pending. Raw log clock has no recorded timezone; no per-method wall duration or benchmark inferred.'),indent=2)+'\n',encoding='utf-8')
print('One completed current development method/eight controls saved, full37 remains running')
