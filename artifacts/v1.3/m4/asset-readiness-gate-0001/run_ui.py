"""Owner-authorized foreground F1 gate; record readiness, then save original reports/PNGs."""
import hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4';ADB=ROOT/'vendor/platform-tools/adb.exe'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'ui-execution-0001.json';assert not target.exists();run=M4/'device-local-assets-ui-0001';assert not run.exists()
for name,phase in [('device-local-assets-0002','CORE'),('device-local-assets-adjacent-0002','ADJACENT')]:
    assert read(HERE/(name+'-verified.json'))['status']=='PASS_F1_'+phase+'_INDEPENDENT_ORIGINAL_CONTRACT_CHECK_NOT_CLOSURE'
for name,value in read(M4/'build-0056/source-at-build-start.json')['files'].items():assert sha(ROOT/name)==value,name
readiness=[]
for service in ['window','power']:
    argv=[str(ADB),'-s','R3CT908DHHR','shell','dumpsys',service]+(['policy'] if service=='window' else [])
    out=subprocess.run(argv,capture_output=True,check=True,timeout=30);value=out.stdout.decode('utf-8',errors='replace')
    lines=[line.strip() for line in value.splitlines() if (re.search(r'^\s*(showing|mIsShowing)=',line) if service=='window' else 'mWakefulness=' in line)]
    readiness.append(dict(argv=argv,returncode=out.returncode,observed=lines))
    assert ('showing=false' in lines and 'mIsShowing=false' in lines) if service=='window' else ('mWakefulness=Awake' in lines), readiness
record=dict(status='RUNNING',recorded_utc=datetime.now(timezone.utc).isoformat(),readiness=readiness,
    owner_quote='Yes, announce when it starts',owner_reply='Actual human reply to call_3c9c03f32a7f47c7bcfc1be8655f3769, announced five-minute window immediately before this prepared test; no radio or unlock modification.',
    ordering_scope='Development core and adjacent background contracts precede this development-only UI. Approved-policy core/adjacent remain independently mandatory before F1 closure, and may follow this foreground window to limit owner waiting. No gate is waived.',commands=[])
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
commands=[
    [sys.executable,'-X','utf8','-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0056'),'--run',str(run),
     '--class-name','org.packrag.product.LocalAssetsUiTest','--result-file','m4-local-assets-ui.json','--timeout','1200'],
    [sys.executable,'-X','utf8','-m','scripts.v13_collect_phone_results','--run',str(run),'--files','m4-local-assets-ui.json']]
for i,argv in enumerate(commands):
    start=datetime.now(timezone.utc).isoformat();print('F1 foreground',i,'START',flush=True)
    with (HERE/f'ui-0001-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'ui-0001-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=err)
    record['commands'].append(dict(argv=argv,started_utc=start,finished_utc=datetime.now(timezone.utc).isoformat(),returncode=result.returncode))
    record['status']='FAIL' if result.returncode else 'RUNNING';target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'Hold F1; preserve failure and completed originals before any switch or repair'
images=read(run/'m4-local-assets-ui.json')['visual_png'];assert set(images)=={'m4-local-assets-generator.png','m4-local-assets-encoder.png'}
for name,expected in images.items():
    argv=[str(ADB),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/'+name]
    output=subprocess.run(argv,capture_output=True,check=True,timeout=30)
    assert hashlib.sha256(output.stdout).hexdigest()==expected['sha256'] and len(output.stdout)==expected['bytes']
    p=run/'original-adb'/name;assert not p.exists();p.write_bytes(output.stdout)
    record['commands'].append(dict(argv=argv,returncode=output.returncode,stderr=output.stderr.decode('utf-8',errors='replace')))
record.update(status='PASS_F1_ACTUAL_UI_ORIGINALS_NOT_VISUAL_OR_CLOSURE',original_png=images)
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'],flush=True)
