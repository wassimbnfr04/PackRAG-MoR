"""Only after owner foreground availability and completed focused gate; originals/PNGs before switches."""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(HERE/'pair-preflight.json')['matched_variants']
assert read(HERE/'focused-device-execution.json')['status']=='PASS_NEW_E2_BACKGROUND_METHODS_ORIGINALS_SAVED_NOT_E2_CLOSURE'
python=[sys.executable,'-X','utf8'];run=M4/'device-ui-source-details-0001'
commands=[python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0039'),'--run',str(run),
    '--class-name','org.packrag.product.SourceDetailsUiTest,org.packrag.product.QueryControlsUiTest,org.packrag.product.PackManagementUiTest',
    '--result-file','m4-source-details-ui.json','--timeout','1800'],
    python+['-m','scripts.v13_collect_phone_results','--run',str(run),'--files',
    'm4-source-details-ui.json,m4-source-details-languages-ui.json,m4-ui-query-controls.json,m3-pack-management-ui.json']]
target=HERE/'ui-execution.json';assert not target.exists();records=[]
for i,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('E2 UI',i,'START',flush=True)
    with (HERE/f'ui-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'ui-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'E2 UI gate failed; stop progression and preserve completed originals before any APK switch'
    print('E2 UI',i,'PASS',flush=True)
images={}
for row in read(run/'m4-source-details-languages-ui.json')['cases']:
    name=row['screenshot'];assert name in ['m4-source-details-ar.png','m4-source-details-fr.png']
    command=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/'+name]
    result=subprocess.run(command,capture_output=True,check=True,timeout=30);assert hashlib.sha256(result.stdout).hexdigest()==row['screenshot_sha256']
    saved=run/'original-adb'/name;assert not saved.exists();saved.write_bytes(result.stdout);images[name]=row['screenshot_sha256']
target.write_text(json.dumps(dict(status='PASS_FOUR_UI_METHODS_ORIGINALS_AND_SCREENSHOTS_SAVED_NOT_VISUAL_OR_E2_CLOSURE',commands=records,
    original_png_sha256=images,foreground_authorization='Owner text reply required before invoking this prepared driver'),indent=2)+'\n',encoding='utf-8')
print('E2_UI_ORIGINALS_AND_PNGS_SAVED_VISUAL_QA_PENDING',flush=True)
