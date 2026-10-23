"""Prepared actual foreground gate; originals and PNGs before any APK switch."""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(HERE/'lifecycle-device-execution.json')['status']=='PASS_E3_REAL_NATIVE_LIFECYCLE_ORIGINAL_NOT_FOREGROUND_OR_COMPLETE_E3'
assert read(HERE/'foreground-retry-readiness.json')['owner_quote']=='GO AHEAD ILL LEAVE THE PHONE UNTOUCHED'
assert read(HERE/'capture-repair-preflight.json')['status']=='PASS_EXACT_PRODUCT_APK_SINGLE_UI_CAPTURE_REPAIR_NOT_NEW_UI_VISUAL_OR_E3_CLOSURE'
python=[sys.executable,'-X','utf8'];run=M4/'device-ui-diagnostic-navigation-0002'
commands=[python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0047'),'--run',str(run),
    '--class-name','org.packrag.product.DiagnosticNavigationUiTest','--result-file','m4-diagnostic-navigation.json','--timeout','900'],
    python+['-m','scripts.v13_collect_phone_results','--run',str(run),'--files','m4-diagnostic-navigation.json']]
target=HERE/'navigation-ui-repaired-execution.json';assert not target.exists();records=[]
for i,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('E3 navigation UI',i,'START',flush=True)
    with (HERE/f'navigation-ui-repaired-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'navigation-ui-repaired-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'Hold E3; preserve foreground failure and all completed outputs before any switch'
    print('E3 navigation UI',i,'PASS',flush=True)
value=read(run/'original-adb/m4-diagnostic-navigation.json');assert value['status']=='PASS' and len(value['cases'])==7
assert all(r['passed'] for r in value['cases']);images={}
for name,row in value['visual_png'].items():
    assert name in ['m4-diagnostic-home.png','m4-diagnostic-source.png']
    command=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/'+name]
    out=subprocess.run(command,capture_output=True,check=True,timeout=30)
    assert len(out.stdout)==row['bytes'] and hashlib.sha256(out.stdout).hexdigest()==row['sha256']
    saved=run/'original-adb'/name;assert not saved.exists();saved.write_bytes(out.stdout);images[name]=row['sha256']
assert len(images)==2
target.write_text(json.dumps(dict(status='PASS_E3_NAVIGATION_UI_ORIGINALS_PNGS_NOT_VISUAL_OR_FULL_E3',commands=records,
    original_png_sha256=images,scope='Actual completed UI, Activity recreation, Android Back injection; independent visual review and full retained/policy acceptance still required.'),indent=2)+'\n',encoding='utf-8')
print('E3_NAVIGATION_UI_SAVED_VISUAL_QA_PENDING',flush=True)
