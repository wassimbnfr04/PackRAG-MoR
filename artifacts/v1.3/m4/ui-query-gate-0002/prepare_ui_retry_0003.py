"""Fresh retry after a build-readiness preflight failure; no device command ran in0002."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).parent;ROOT=HERE.parents[3];M4=ROOT/'artifacts/v1.3/m4'
failure=json.loads((M4/'device-ui-query-0002/instrumentation-manifest.json').read_text())
assert failure['status']=='FAIL' and failure['commands']==[]
assert json.loads((M4/'build-0035/build-result.json').read_text(encoding='utf-8-sig'))['exit_code']==0
old=(HERE/'run_ui_repaired.py').read_bytes();new=old.decode('utf-8').replace('device-ui-query-0002','device-ui-query-0003').replace('ui-execution-0002.json','ui-execution-0003.json').replace('ui0002-stage-{i}','ui0003-stage-{i}')
destination=HERE/'run_ui_retry_0003.py';assert not destination.exists();destination.write_text(new,encoding='utf-8');compile(new,str(destination),'exec')
record=HERE/'ui-readiness-failure.json';assert not record.exists()
record.write_text(json.dumps(dict(recorded_utc=datetime.now(timezone.utc).isoformat(),status='RUNNER_PREFLIGHT_FAILED_BEFORE_DEVICE_COMMAND_NO_PHONE_TEST_RUN',
    cause='Retry was invoked before async debug0035 build completed; build-result.json did not yet exist. Waited for actual successful completion before fresh0003.',
    no_test_killed=True,product_code_changed=False,old_runner_sha256=hashlib.sha256(old).hexdigest(),new_runner_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
    prior_run='device-ui-query-0002',new_run='device-ui-query-0003',
    scheduling='Demo0036 was started while the last debug0035 build tasks were finishing. Both use frozen identical sources and separate variant outputs; compare complete input/APK identities. Subsequent Gradle jobs must be sequential.'),indent=2)+'\n')
print('Fresh0003 prepared after actual build readiness')
