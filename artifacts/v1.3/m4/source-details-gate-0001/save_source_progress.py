"""Bound early source-method reports; explicitly not a completed full JUnit gate."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
target=M4/'source-details-progress-0001';assert not target.exists()
adb=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR'];names=['m4-source-details-rows.json','m4-source-details-rejections.json']
commands=[];payloads={}
for name in names:
    command=adb+['exec-out','run-as','org.packrag.product','cat','files/'+name]
    result=subprocess.run(command,capture_output=True,check=True,timeout=30)
    value=json.loads(result.stdout);assert value['status']=='PASS'
    commands.append(dict(argv=command,returncode=result.returncode,stderr_utf8=result.stderr.decode('utf-8',errors='replace')));payloads[name]=result.stdout
logs=subprocess.run(adb+['logcat','-d','-s','TestRunner:I','AndroidJUnitRunner:I','*:S'],capture_output=True,check=True,timeout=30).stdout
tail=logs.decode('utf-8',errors='replace').split('run started: 35 tests')[-1]
assert 'finished: installedTamperIdentityMissingAndRemovedDetailsFailWithoutMutation' in tail
assert 'finished: originalSignedRowsActiveInactiveInspectionAndOwnedCopies' in tail
assert 'started: actualAnswerContextSurvivesInspectionAndMutationClearsDetails' in tail
target.mkdir();raw=target/'original-adb';raw.mkdir()
for name,value in payloads.items():(raw/name).write_bytes(value)
(target/'test-runner-source-progress.txt').write_text('run started: 35 tests'+tail,encoding='utf-8')
build=M4/'build-0041';apks={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in build.glob('*.apk')}
(target/'record.json').write_text(json.dumps(dict(status='OBSERVED_COMPLETED_SOURCE_METHOD_REPORTS_NOT_FULL_JUNIT_OR_E2_ACCEPTANCE',
    recorded_utc=datetime.now(timezone.utc).isoformat(),pending_run='device-source-details-full-0001',build='build-0041',apk_sha256=apks,
    saved_sha256={name:hashlib.sha256(value).hexdigest() for name,value in payloads.items()},commands=commands,
    scope='Early original reports after current TestRunner source-method completion; real ViewModel/full35 methods are still running. Final acceptance requires full manifest, original collector and parity.'),indent=2)+'\n',encoding='utf-8')
print('Saved two early original source-method reports; complete35-method gate still pending')
