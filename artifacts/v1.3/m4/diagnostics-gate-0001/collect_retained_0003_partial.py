"""Fail-suite custody of only completed passing methods, before APK switch."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;run=ROOT/'artifacts/v1.3/m4/device-ui-diagnostics-retained-0003'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
manifest=read(run/'instrumentation-manifest.json');assert manifest['status']=='FAIL'
text=(run/'instrumentation.txt').read_text(encoding='utf-8');assert 'Tests run: 4,' in text
blocks=text.split('INSTRUMENTATION_STATUS_CODE:');methods={}
for i,block in enumerate(blocks[:-1]):
    match=re.search(r'INSTRUMENTATION_STATUS: test=(\w+)',block)
    if match:methods[match[1]]=int(blocks[i+1].splitlines()[0].strip())
assert len(methods)==4 and any(v<0 for v in methods.values())
mapping={'realAnswerCanonicalDetailsActiveInactiveAndSharedMutationControls':'m4-source-details-ui.json',
    'verifiedArabicFrenchCanonicalAndEnglishRenderingComponentScreenshots':'m4-source-details-languages-ui.json',
    'capturedControlsSurviveRealGenerationEditsRecreationAndSourceNavigation':'m4-ui-query-controls.json',
    'isolatedPackControlsWarningsRemovalAndRestart':'m3-pack-management-ui.json'}
assert set(methods)==set(mapping)
raw=run/'original-adb';assert not raw.exists();raw.mkdir();saved={};commands=[]
def adb(args):
    argv=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR']+args
    result=subprocess.run(argv,capture_output=True,check=True,timeout=30);commands.append(dict(argv=argv,returncode=result.returncode));return result.stdout
logs=adb(['logcat','-d','-s','TestRunner:I']).decode('utf-8',errors='replace')
logs='\n'.join(line for line in logs.splitlines() if re.search(r'\s21759\s',line))+'\n'
assert 'run finished: 4 tests,' in logs;(run/'completed-test-runner.txt').write_text(logs,encoding='utf-8')
for method,name in mapping.items():
    if methods[method]!=0:continue
    assert 'finished: '+method in logs and 'failed: '+method not in logs
    data=adb(['shell','run-as','org.packrag.product','cat','files/'+name]);value=json.loads(data)
    assert value['status']=='PASS' and all(row['passed'] for row in value['cases'])
    (raw/name).write_bytes(data);(run/name).write_bytes(data);saved[name]=hashlib.sha256(data).hexdigest()
if methods['verifiedArabicFrenchCanonicalAndEnglishRenderingComponentScreenshots']==0:
    for row in read(run/'m4-source-details-languages-ui.json')['cases']:
        name=row['screenshot'];assert name in ['m4-source-details-ar.png','m4-source-details-fr.png']
        data=adb(['exec-out','run-as','org.packrag.product','cat','files/'+name]);assert hashlib.sha256(data).hexdigest()==row['screenshot_sha256']
        (raw/name).write_bytes(data);saved[name]=row['screenshot_sha256']
if methods['capturedControlsSurviveRealGenerationEditsRecreationAndSourceNavigation']==0:
    name='m4-ui-query-resubmission-observation.json';data=adb(['shell','run-as','org.packrag.product','cat','files/'+name]);value=json.loads(data)
    assert value['status']=='PASS_NEW_COMPLETION_EDITED_CONTEXT_ABSTENTION' and value['new_completion_id']!=value['previous_completion_id'] and value['new_answer_state']=='NO_RELEVANT_EVIDENCE'
    (raw/name).write_bytes(data);(run/name).write_bytes(data);saved[name]=hashlib.sha256(data).hexdigest()
target=run/'partial-collected-results.json';assert not target.exists()
target.write_text(json.dumps(dict(status='SAVED_COMPLETED_PASSING_METHODS_OVERALL_SUITE_FAIL',recorded_utc=datetime.now(timezone.utc).isoformat(),method_status_codes=methods,
    original_sha256=saved,commands=commands,scope='Only JUnit status0 methods with actual report-write source are collected as fresh; failed method reports may be stale and are never promoted. Overall suite FAIL unchanged.'),indent=2)+'\n',encoding='utf-8')
print(json.dumps(methods))
