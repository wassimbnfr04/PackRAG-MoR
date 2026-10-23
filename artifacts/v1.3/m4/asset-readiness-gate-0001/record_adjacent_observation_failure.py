"""Preserve observed guard failure while remaining current tests finish; no new tests."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
target=HERE/'adjacent-observed-guard-failure.json';assert not target.exists()
folder=HERE/'progress/device-local-assets-adjacent-0001'
source=sorted(folder.glob('*.json'))[-1];observation=json.loads(source.read_text())
text=observation['commands'][-1]['stdout'];assert 'failed: actualStaleAnswerOwnsContextJurisdictionExcludesAndPackChangeClearsIt' in text
assert 'QueryControlsDeviceTest.withModel(QueryControlsDeviceTest.kt:43)' in text
adb=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR']
argv=adb+['shell','dumpsys','activity','activities'];result=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',errors='replace',check=True,timeout=30)
lines=[line for line in result.stdout.splitlines() if 'mResumedActivity' in line or 'topResumedActivity' in line]
foreground=['PACKRAG_MAIN_ACTIVITY' if 'org.packrag.product/.MainActivity' in line else 'OTHER_OR_UNRESOLVED_COMPONENT' for line in lines]
record=dict(status='OBSERVED_ADJACENT_OWNER_GUARD_FAILURE_CURRENT_SUITE_STILL_RUNNING',recorded_utc=datetime.now(timezone.utc).isoformat(),
    observation_file=source.relative_to(ROOT).as_posix(),observation_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    observed_failure='QueryControlsDeviceTest.withModel guard equality at line43 after runtime body; full terminal stdout/map diff required.',
    foreground=dict(argv=argv,returncode=result.returncode,classification=foreground,limit='Only component classification is saved; other app titles/URIs and unrelated task details are discarded. This later foreground observation is not causal proof of the earlier guard change.'),
    next='Finish current suite, preserve terminal FAIL and passing originals, compare current owner guards and registry bytes; no new phase, APK switch or source edit before this suite finishes.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
note=f'F1 adjacent guard FAILURE OBSERVED at {record["recorded_utc"]}: actual runtime QueryControls body reaches final withModel owner equality at line43 and reports mismatch. Current five-method suite continues its already started remaining tests; do not kill or change579 sources/APKs. No UI/policy/F2 progression. Full terminal result, passing original custody, exact owner file diff and activity/context diagnosis must precede any repair/retry. Later foreground classification is observational, not causal proof. Prior successful core scope and earlier hardlink failure remain immutable.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;head,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(head+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(record['status'],foreground)
