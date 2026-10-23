"""One frozen foreground class; originals and PNGs saved before any next class/switch."""
import argparse,hashlib,json,re,struct,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4';ADB=ROOT/'vendor/platform-tools/adb.exe'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
plans={
 'query':('QueryControlsUiTest',1,{'m4-ui-query-controls.json':5},[]),
 'management':('PackManagementUiTest',1,{'m3-pack-management-ui.json':7},[]),
 'sources':('SourceDetailsUiTest',2,{'m4-source-details-ui.json':5,'m4-source-details-languages-ui.json':2},['m4-source-details-ar.png','m4-source-details-fr.png']),
 'diagnostics':('DiagnosticNavigationUiTest',1,{'m4-diagnostic-navigation.json':7},['m4-diagnostic-home.png','m4-diagnostic-source.png']),
 'assets':('LocalAssetsUiTest',1,{'m4-local-assets-ui.json':5},['m4-local-assets-generator.png','m4-local-assets-encoder.png'])}
parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);parser.add_argument('--run',required=True);parser.add_argument('--selection',choices=plans,required=True);parser.add_argument('--foreground-authorized',required=True,action='store_true');args=parser.parse_args()
target=HERE/(args.run+'-execution.json');run=M4/args.run;build=M4/args.build
assert target.parent==HERE and run.parent==M4 and build.parent==M4 and not target.exists() and not run.exists()
background=HERE/'device-local-asset-adjacent-debug-0001-execution.json'
assert read(background)['status']=='PASS_F2_FRESH_ADJACENT_BACKGROUND_VARIANT_NOT_FULL_F2' and read(background)['build']==args.build
assert read(HERE/(args.build+'-capture.json'))['variant']=='debug'
pair=read(HERE/'adjacent-source-pair-0001.json');sources=read(build/'source-at-build-start.json')['files'];assert sources==pair['android_source_sha256']
for name,value in sources.items():assert sha(ROOT/name)==value,name
class_name,methods,files,pngs=plans[args.selection];primary=next(iter(files));baseline=read(HERE/'before.json')['owner_public_file_sha256']
record=dict(status='RUNNING_F2_FOREGROUND_ADJACENT_NOT_ACCEPTED',started_utc=datetime.now(timezone.utc).isoformat(),runner_sha256=sha(Path(__file__)),build=args.build,run=args.run,selection=args.selection,foreground_authorized=True,background_sha256=sha(background),commands=[])
def command(argv,label):
    print(args.run,label,'START',flush=True)
    with (HERE/(args.run+'-'+label+'.stdout.txt')).open('xb') as out,(HERE/(args.run+'-'+label+'.stderr.txt')).open('xb') as err:
        result=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=err)
    record['commands'].append(dict(argv=argv,returncode=result.returncode))
    target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'Hold F2/F3; preserve failed run first'
    print(args.run,label,'PASS',flush=True)
try:
    command([sys.executable,'-X','utf8',str(HERE/'test_android_installed_0001.py'),'--serial','R3CT908DHHR','--build',str(build),'--run',str(run),'--class-name','org.packrag.product.'+class_name,'--result-file',primary,'--timeout','1800','--variant','debug'],'instrumentation')
    command([sys.executable,'-X','utf8','-m','scripts.v13_collect_phone_results','--run',str(run),'--files',','.join(files)],'collect')
    manifest=read(run/'instrumentation-manifest.json');assert manifest['status']=='PASS' and manifest['transport']=='VERIFY_EXACT_INSTALLED_APKS_NO_REINSTALL'
    assert re.search(r'OK \('+str(methods)+r' tests?\)',(run/'instrumentation.txt').read_text())
    collection=read(run/'collected-results.json');assert set(collection['saved_sha256'])==set(files)
    image_metadata={}
    for name,count in files.items():
        path=run/'original-adb'/name;assert sha(path)==collection['saved_sha256'][name];value=read(path)
        assert value['status']=='PASS' and len(value['cases'])==count and all(case['passed'] is True for case in value['cases'])
        assert value['owner_registry_and_model_sha256']==baseline and value['owner_guard_scope']=='EXPLICIT_50_PUBLIC_BASELINE_FILES_NO_ENUMERATION'
        if 'raw_reasoning_persisted' in value:assert value['raw_reasoning_persisted'] is False
        if 'answer' in value:assert '74 °C' in value['answer'] and '[S1]' in value['answer'] and '</think>' not in value['answer']
        image_metadata.update(value.get('visual_png',{}))
        for case in value['cases']:
            if 'screenshot' in case:image_metadata[case['screenshot']]={'sha256':case['screenshot_sha256']}
    assert set(image_metadata)==set(pngs)
    saved={}
    for name in pngs:
        result=subprocess.run([str(ADB),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/'+name],capture_output=True,timeout=30)
        path=run/'original-adb'/name;path.write_bytes(result.stdout)
        assert result.returncode==0 and result.stdout.startswith(b'\x89PNG\r\n\x1a\n')
        assert sha(path)==image_metadata[name]['sha256']
        if 'bytes' in image_metadata[name]:assert len(result.stdout)==image_metadata[name]['bytes']
        saved[name]=dict(sha256=sha(path),bytes=len(result.stdout),dimensions=struct.unpack('>II',result.stdout[16:24]))
    if args.selection=='query':
        name='m4-ui-query-resubmission-observation.json'
        result=subprocess.run([str(ADB),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/'+name],capture_output=True,timeout=30)
        path=run/'original-adb'/name;path.write_bytes(result.stdout);observation=json.loads(result.stdout)
        assert result.returncode==0 and observation['status']=='PASS_NEW_COMPLETION_EDITED_CONTEXT_ABSTENTION'
        record['resubmission_observation_sha256']=sha(path)
    command([sys.executable,'-X','utf8',str(HERE/'capture_known_guard.py'),'--output',args.run+'-after-known.json'],'after-known')
    for name,value in sources.items():assert sha(ROOT/name)==value,name
    record.update(status='PASS_F2_FRESH_FOREGROUND_ADJACENT_CONTRACTS_VISUAL_REVIEW_PENDING_NOT_FULL_F2',methods=methods,controls=sum(files.values()),original_sha256=collection['saved_sha256'],pngs=saved,
        scope='Actual frozen class and exact original reports/PNG bytes; all functional assertions retained after guard-only repair. Independent visible-scope image review mandatory for classes with PNGs; classes without PNGs establish actual UI assertions, not new visual exports. AR/FR are separately disclosed verified viewer-component controls with setContent, not production pack admission/new inference. No reinstalls, owner data/radio writes, performance/gold/full F2/M4/product/release claim.')
except Exception as failure:
    record.update(status='FAIL_HOLD_F2_F3',failure_type=type(failure).__name__,failure_message=str(failure))
    if run.exists():
        directory=run/'failure-original-adb';directory.mkdir(exist_ok=False);captures={}
        for name in list(files)+pngs:
            result=subprocess.run([str(ADB),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/'+name],capture_output=True,timeout=30)
            path=directory/name;path.write_bytes(result.stdout)
            info=dict(returncode=result.returncode,sha256=sha(path),bytes=len(result.stdout),scope='Possibly stale/unaccepted previous report or command-error bytes; never promote to new PASS.')
            if name.endswith('.png'):info['valid_png_signature']=result.stdout.startswith(b'\x89PNG\r\n\x1a\n')
            else:
                try:info.update(valid_json=True,reported_status=json.loads(result.stdout).get('status'))
                except (ValueError,UnicodeError):info['valid_json']=False
            captures[name]=info
        record['failure_captures']=captures
    raise
finally:
    record['finished_utc']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(record['status'],flush=True)
