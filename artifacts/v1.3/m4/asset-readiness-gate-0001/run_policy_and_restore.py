"""Only after actual development/UI/visual success, run policy then restore serially.

Every device-original collector completes before the next APK installation.
Any failure stops progression and retains completed outputs. Not F1 closure.
"""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'policy-and-restoration-execution-0001.json';assert not target.exists()
for name,phase in [('device-local-assets-0002','CORE'),('device-local-assets-adjacent-0002','ADJACENT')]:
    assert read(HERE/(name+'-verified.json'))['status']=='PASS_F1_'+phase+'_INDEPENDENT_ORIGINAL_CONTRACT_CHECK_NOT_CLOSURE'
assert read(HERE/'ui-execution-0001.json')['status']=='PASS_F1_ACTUAL_UI_ORIGINALS_NOT_VISUAL_OR_CLOSURE'
visual=read(HERE/'ui-visual-0001.json');assert visual['status']=='PASS_F1_ORIGINAL_ASSET_SCREEN_TESTED_VIEWPORT'
ui=M4/'device-local-assets-ui-0001';assert read(ui/'instrumentation-manifest.json')['status']=='PASS'
for name,value in visual['original_png_sha256'].items():assert sha(ui/'original-adb'/name)==value
inputs=read(M4/'build-0056/source-at-build-start.json')['files'];assert len(inputs)==579
assert inputs==read(M4/'build-0057/source-at-build-start.json')['files']
for name,value in inputs.items():assert sha(ROOT/name)==value,name
restored=M4/'device-local-assets-development-restore-0001'
for folder in [M4/'device-local-assets-policy-0001',M4/'device-local-assets-policy-adjacent-0001',restored]:assert not folder.exists(),folder
assert not (HERE/'current-source-at-closure.json').exists() and not (HERE/'owner-at-closure.json').exists()
python=[sys.executable,'-X','utf8'];commands=[]
for name,phase in [('device-local-assets-policy-0001','core'),('device-local-assets-policy-adjacent-0001','adjacent')]:
    commands.append(python+[str(HERE/'run_background.py'),'--build','build-0057','--run',name,'--variant','demo','--phase',phase])
    commands.append(python+[str(HERE/'verify_background.py'),'--run',name])
commands.extend([
    python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0056'),'--run',str(restored),
        '--class-name','org.packrag.product.PackImportConsentTest','--result-file','m3-import-consent.json','--timeout','900','--variant','debug'],
    python+['-m','scripts.v13_collect_phone_results','--run',str(restored),'--files','m3-import-consent.json'],
    python+['-m','scripts.v13_android_source_identity','--output',str(HERE/'current-source-at-closure.json')],
    python+[str(HERE/'capture_owner_at_closure.py')]])
record=dict(status='RUNNING',started_utc=datetime.now(timezone.utc).isoformat(),commands=[],
    scope='Serial actual approved-policy core/adjacent with all originals before switching; restore tested development product and consent original; check actual final source/known owner-file guards. Requires independently completed development/UI/visual gates. No radios, private custody or owner data reset. Any failure holds F1; no F2 start.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
for i,argv in enumerate(commands):
    started=datetime.now(timezone.utc).isoformat();print('F1 policy/restoration stage',i,'START',flush=True)
    with (HERE/f'policy-restoration-0001-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'policy-restoration-0001-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=err)
    record['commands'].append(dict(argv=argv,started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),returncode=result.returncode))
    record['status']='FAIL' if result.returncode else 'RUNNING';target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'Hold F1; preserve actual failure and originals before any repair or switch'
    print('F1 policy/restoration stage',i,'PASS',flush=True)
record.update(status='PASS_F1_POLICY_ORIGINALS_RESTORATION_AND_FINAL_GUARDS_NOT_CLOSURE',finished_utc=datetime.now(timezone.utc).isoformat())
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'],flush=True)
