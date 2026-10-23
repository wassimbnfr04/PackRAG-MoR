"""Collect only three completed methods; overall retry remains FAIL."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
run=ROOT/'artifacts/v1.3/m4/device-ui-diagnostics-retained-0002'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(run/'instrumentation-manifest.json')['status']=='FAIL'
terminal=(run/'instrumentation.txt').read_text(encoding='utf-8').rsplit('INSTRUMENTATION_RESULT: stream=',1)[1]
assert 'Tests run: 4,  Failures: 1' in terminal and 'QueryControlsUiTest.kt:81' in terminal
target=run/'partial-collected-results.json';assert not target.exists()
raw=run/'original-adb';raw.mkdir(exist_ok=False);commands=[];saved={}
def adb(args):
    argv=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR']+args
    result=subprocess.run(argv,capture_output=True,check=True,timeout=30)
    commands.append(dict(argv=argv,returncode=result.returncode));return result.stdout
logs=adb(['logcat','-d','-s','TestRunner:I']).decode('utf-8',errors='replace')
logs='\n'.join(line for line in logs.splitlines() if re.search(r'\s10004\s',line))+'\n'
assert 'run finished: 4 tests, 1 failed, 0 ignored' in logs
for method in ['realAnswerCanonicalDetailsActiveInactiveAndSharedMutationControls','verifiedArabicFrenchCanonicalAndEnglishRenderingComponentScreenshots','isolatedPackControlsWarningsRemovalAndRestart']:
    assert 'finished: '+method in logs and 'failed: '+method not in logs
(run/'completed-test-runner.txt').write_text(logs,encoding='utf-8')
for name in ['m4-source-details-ui.json','m4-source-details-languages-ui.json','m3-pack-management-ui.json']:
    data=adb(['shell','run-as','org.packrag.product','cat','files/'+name]);value=json.loads(data)
    assert value['status']=='PASS' and all(row['passed'] for row in value['cases'])
    if name!='m3-pack-management-ui.json':assert value['raw_reasoning_persisted'] is False
    else:assert len(value['cases'])==7 and value['isolated_registry']
    (raw/name).write_bytes(data);saved[name]=hashlib.sha256(data).hexdigest()
    (run/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
for row in read(run/'m4-source-details-languages-ui.json')['cases']:
    name=row['screenshot'];assert name in ['m4-source-details-ar.png','m4-source-details-fr.png']
    data=adb(['exec-out','run-as','org.packrag.product','cat','files/'+name])
    assert hashlib.sha256(data).hexdigest()==row['screenshot_sha256']
    (raw/name).write_bytes(data);saved[name]=row['screenshot_sha256']
target.write_text(json.dumps(dict(status='SAVED_THREE_COMPLETED_METHODS_OVERALL_SUITE_FAIL',recorded_utc=datetime.now(timezone.utc).isoformat(),original_sha256=saved,commands=commands,
    failed_method='capturedControlsSurviveRealGenerationEditsRecreationAndSourceNavigation',not_collected_as_new=['m4-ui-query-controls.json'],
    failure='Expected NO_RELEVANT_EVIDENCE, observed ANSWER_ACCEPTED at final resubmission assertion. No cause claimed before diagnosis; no stale failed-method JSON promoted.'),indent=2)+'\n',encoding='utf-8')
print('Three original passing-method reports and two PNGs saved; overall suite FAIL preserved')
