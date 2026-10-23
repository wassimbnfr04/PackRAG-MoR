"""Save only outputs of completed passing methods in an overall FAILED UI run."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4';run=M4/'device-ui-diagnostics-retained-0001';ADB=ROOT/'vendor/platform-tools/adb.exe'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(HERE/'retained-ui-execution.json')['status']=='FAIL' and read(run/'instrumentation-manifest.json')['status']=='FAIL'
text=(run/'instrumentation.txt').read_text(encoding='utf-8');assert 'Tests run: 4,  Failures: 2' in text and text.rsplit('INSTRUMENTATION_RESULT: stream=',1)[1].count('No compose hierarchies found')==2
raw=run/'original-adb';assert raw.is_dir() and {p.name for p in raw.iterdir()}=={"m4-source-details-languages-ui.json"};commands=[];saved={}
def adb(label,args):
    argv=[str(ADB),'-s','R3CT908DHHR']+args;result=subprocess.run(argv,capture_output=True,check=True,timeout=30)
    commands.append(dict(label=label,argv=argv,returncode=result.returncode));return result.stdout
logs=adb('completed-test-runner',['logcat','-d','-s','TestRunner:I']).decode('utf-8',errors='replace')
lines=[line for line in logs.splitlines() if re.search(r'\s30729\s',line)];logs='\n'.join(lines)+'\n'
assert 'run finished: 4 tests, 2 failed, 0 ignored' in logs
for method in ['verifiedArabicFrenchCanonicalAndEnglishRenderingComponentScreenshots','isolatedPackControlsWarningsRemovalAndRestart']:
    assert 'finished: '+method in logs and 'failed: '+method not in logs
p=run/'completed-test-runner.txt';assert p.read_text(encoding='utf-8')==logs
for name in ['m4-source-details-languages-ui.json','m3-pack-management-ui.json']:
    data=adb('completed-method-original',['shell','run-as','org.packrag.product','cat','files/'+name]);value=json.loads(data)
    assert value['status']=='PASS' and all(row['passed'] for row in value['cases'])
    if name=='m4-source-details-languages-ui.json':assert value['raw_reasoning_persisted'] is False
    else:assert len(value['cases'])==7 and value['isolated_registry'] and 'raw_reasoning_persisted' not in value
    original=raw/name
    if original.exists():assert original.read_bytes()==data
    else:original.write_bytes(data)
    saved[name]=hashlib.sha256(data).hexdigest()
    primary=run/name
    if primary.exists():assert read(primary)==value
    else:primary.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
for row in read(run/'m4-source-details-languages-ui.json')['cases']:
    name=row['screenshot'];assert name in ['m4-source-details-ar.png','m4-source-details-fr.png']
    data=adb('completed-component-original-png',['exec-out','run-as','org.packrag.product','cat','files/'+name])
    assert hashlib.sha256(data).hexdigest()==row['screenshot_sha256'];(raw/name).write_bytes(data);saved[name]=row['screenshot_sha256']
focus=adb('completed-run-current-focus',['shell','dumpsys','window']).decode('utf-8',errors='replace')
focus='\n'.join(line for line in focus.splitlines() if 'mCurrentFocus=' in line or 'mFocusedApp=' in line)+'\n'
(run/'completed-current-focus.txt').write_text(focus,encoding='utf-8')
record=dict(status='SAVED_TWO_COMPLETED_PASSING_METHODS_OVERALL_FOUR_METHOD_SUITE_FAIL',recorded_utc=datetime.now(timezone.utc).isoformat(),
    original_sha256=saved,commands=commands,failed_methods=['realAnswerCanonicalDetailsActiveInactiveAndSharedMutationControls','capturedControlsSurviveRealGenerationEditsRecreationAndSourceNavigation'],
    not_collected_as_new=['m4-source-details-ui.json','m4-ui-query-controls.json'],
    diagnosis='Two No compose hierarchies found exceptions after actual generation. PackRAG window stopped while queries ran; Firefox foreground observed independently. Screen interruption is supported, but its actor/cause is not proved. No production/source/assertion change for fresh retry.',
    scope='These two fresh JSONs and component PNGs belong only to completed passing methods; suite remains FAIL. Missing failed-method reports may be stale on phone and are not promoted. No visual or full E3 acceptance.')
target=run/'partial-collected-results.json';assert not target.exists();target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
