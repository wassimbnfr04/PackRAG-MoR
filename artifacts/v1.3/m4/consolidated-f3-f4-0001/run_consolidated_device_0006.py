"""Fixed final-source physical matrix. Serial classes, original bytes, hold on first failure."""
import argparse,hashlib,json,re,shlex,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4';ADB=ROOT/'vendor/platform-tools/adb.exe'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
parser=argparse.ArgumentParser();parser.add_argument('--phase',required=True);parser.add_argument('--prefix',required=True);parser.add_argument('--installed-proof',required=True);parser.add_argument('--foreground-window');args=parser.parse_args()
assert re.fullmatch('[a-z0-9-]+',args.prefix)
planpath=HERE/'device-matrix-0006.json';plan=read(planpath);assert args.phase in plan['phases']
is_ui=args.phase in {'debug-ui','debug-ui-remaining'}
variant=args.phase.split('-')[0];buildname=plan[variant+'_build'];build=M4/buildname
proof=HERE/args.installed_proof;assert proof.parent==HERE
install=read(proof);assert install['status']=='PASS_SERIAL_INSTALLED_EXACT_APK_PAIR_NO_TEST_ACCEPTANCE' and install['build']==buildname and install['variant']==variant
pairpath=HERE/'source-pair-0005.json';pair=read(pairpath);assert sha(pairpath)==plan['pair_sha256'] and pair['status']=='PASS_MATCHED_CONSOLIDATED_623_HOST91_BUILDS_NOT_PHONE_ACCEPTANCE'
sources=pair['android_source_sha256'];assert read(build/'source-at-build-start.json')['files']==sources
baseline=read(HERE/'before.json')['owner_public_file_sha256'];assert len(baseline)==50
classes=plan['phases'][args.phase];target=HERE/(args.prefix+'-execution.json');assert not target.exists()
record={'status':'RUNNING_CONSOLIDATED_PHASE_NOT_M4_ACCEPTANCE','started_utc':utc(),'phase':args.phase,'build':buildname,'variant':variant,'runner_sha256':sha(Path(__file__)),'matrix_sha256':sha(planpath),'pair_sha256':sha(pairpath),'installation_sha256':sha(proof),'classes':classes,'commands':[],'completed':[]}
current=None;names=[];sidecars=[];pngs=[]
window=None
if is_ui:
    assert args.foreground_window,'A fresh explicitly authorized untouched window is required'
    wp=HERE/args.foreground_window;assert wp.parent==HERE
    window=read(wp);assert window['status']=='OWNER_AUTHORIZED_ANNOUNCED_FOREGROUND_WINDOW_NOT_ACCEPTANCE'
    assert window['build']==buildname and window['matrix_sha256']==sha(planpath)
    launch_epoch=window.get('continuation_created_monotonic',window['started_monotonic'])
    assert 0<=time.monotonic()-launch_epoch<=120 and time.monotonic()<window['deadline_monotonic']
    if 'original_window' in window:
        original_path=HERE/window['original_window'];assert original_path.parent==HERE and sha(original_path)==window['original_window_sha256']
        original=read(original_path);assert window['started_monotonic']==original['started_monotonic']
        if 'deadline_extension_human_reply' in window:
            assert window['deadline_extension_human_reply']=='Yes, continue until 16:48'
            assert original['deadline_monotonic']<window['deadline_monotonic']<=original['deadline_monotonic']+1800
        else:assert window['deadline_monotonic']==original['deadline_monotonic']
    record['foreground_window_sha256']=sha(wp)
else:assert args.foreground_window is None
def save():target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
def unchanged():
    for name,value in sources.items():assert sha(ROOT/name)==value,name
    for cl in classes:assert sha(ROOT/plan['entries'][cl]['source'])==plan['entries'][cl]['source_sha256'],cl
def command(argv,label):
    print(args.prefix,label,'START',flush=True)
    with (HERE/(args.prefix+'-'+label+'.stdout.txt')).open('xb') as out,(HERE/(args.prefix+'-'+label+'.stderr.txt')).open('xb') as err:
        result=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=err)
    record['commands'].append({'argv':argv,'returncode':result.returncode,'label':label});save()
    assert result.returncode==0,'Failed '+label+'; hold later classes'
    print(args.prefix,label,'PASS',flush=True)
def adb_read(name):
    assert re.fullmatch(r'[A-Za-z0-9_.-]+\.(json|png)',name)
    argv=[str(ADB),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/'+name]
    return subprocess.run(argv,capture_output=True,timeout=30)
def guard(label):
    command([sys.executable,'-X','utf8',str(HERE/'capture_owner_no_follow_0001.py'),'--output',args.prefix+'-'+label+'-owner50.json'],label+'-owner50')
    command([sys.executable,'-X','utf8',str(HERE/'verify_source4_0001.py'),'--build',buildname,'--output',args.prefix+'-'+label+'-source4.json','--verify-only'],label+'-source4')
    command([sys.executable,'-X','utf8',str(HERE/'capture_source4_modes_0001.py'),'--output',args.prefix+'-'+label+'-source4-modes.json'],label+'-source4-modes')
def validate(value,spec):
    assert value['status']=='PASS',spec['name']
    for key,expected in spec['fixed_fields'].items():assert value[key]==expected,(spec['name'],key,expected)
    for key,a in spec['arrays'].items():
        rows=value[key];assert len(rows)==a['count'],(spec['name'],key,len(rows),a['count'])
        if 'identity_key' in a:
            ids=[row[a['identity_key']] for row in rows];assert len(set(ids))==len(ids)
            if 'identities' in a:assert ids==a['identities'],(spec['name'],key,'ID sequence')
        if 'pass_key' in a:assert all(row[a['pass_key']]==a['pass_value'] for row in rows)
        if 'accepted' in a:assert [row['accepted'] for row in rows]==a['accepted']
    if 'variant' in value:assert value['variant']==variant
    if 'raw_reasoning_persisted' in value:assert value['raw_reasoning_persisted'] is False
    if 'owner_registry_and_model_sha256' in value:assert value['owner_registry_and_model_sha256']==baseline
    if 'guards_unchanged' in value:assert value['guards_unchanged'] is True
    if spec['name'].startswith('m4-f3-'):assert value['actual_weight_inference'] is False
    if spec['name']=='m4-source-details-languages-ui.json':assert [c['language'] for c in value['cases']]==['ar','fr']
    if spec['name']=='product-runtime-smoke.json':
        case=value['cases'][1];assert case['id']=='SUPPORTED_REAL_INFERENCE' and case['state']=='ANSWER_ACCEPTED'
        assert '74 °C' in case['answer'] and '[S1]' in case['answer'] and '</think>' not in case['answer']
        assert 1<=case['emitted_tokens_including_terminal']<=512 and value['actual_weight_inference'] is True
    if 'observed_partial_copy_bytes' in value:
        assert value['observed_partial_copy_bytes']==128
        for key in ['reading_cancel_dispatch_ms','opening_cancel_dispatch_ms']:assert 0<value[key]<1000
        for label in ['before','after']:
            assert '74 °C' in value['answer_'+label] and '[S1]' in value['answer_'+label] and 1<=value['emitted_tokens_'+label]<=512
        assert value['completed_result_id_before']!=value['completed_result_id_after'] and value['initialization_ms_after']>0
try:
    unchanged()
    if args.phase=='debug-ui-remaining':
        rp=HERE/'retained-ui-after-scroll-repair-0001.json';retention=read(rp)
        assert retention['status']=='PASS_DATED_FIVE_UI_METHODS27_CONTROLS_RETAINED_NOT_NEW_EXECUTION'
        assert retention['current_build']==buildname and retention['current_product_apk_sha256']==sha(build/'app-debug.apk')
        record['retained_ui_review_sha256']=sha(rp)
    save();guard('before')
    for cl in classes:
        if window is not None and time.monotonic()>=window['deadline_monotonic']:
            record.update(status='FOREGROUND_WINDOW_ENDED_BETWEEN_CLASSES_NOT_ACCEPTANCE',next_class=cl);save();print(record['status'],flush=True);sys.exit(0)
        if (HERE/(args.prefix+'-stop-after-current.request')).exists():
            record.update(status='STOPPED_BETWEEN_CLASSES_BY_EXPLICIT_REQUEST_NOT_ACCEPTANCE',next_class=cl,stop_request=(HERE/(args.prefix+'-stop-after-current.request')).read_text(encoding='utf-8'));save();print(record['status'],flush=True);sys.exit(0)
        unchanged();entry=plan['entries'][cl];current=M4/(args.prefix+'-'+cl.lower());assert not current.exists()
        names=[s['name'] for s in entry['reports']]
        sidecars=[name for s in entry['reports'] for name in s.get('sidecars',[])]
        source=(ROOT/entry['source']).read_text(encoding='utf-8')
        pngs=sorted(set(re.findall(r'"([A-Za-z0-9_.-]+\.png)"',source))) if is_ui else []
        if is_ui and cl=='SourceDetailsUiTest':pngs=sorted(set(pngs+['m4-source-details-ar.png','m4-source-details-fr.png']))
        record.update(active_class=cl,active_expected_methods=entry['methods']);save()
        # Save prior exact named testing outputs before clearing them. This prevents stale PASS reuse.
        previous=HERE/(args.prefix+'-'+cl.lower()+'-preexisting');previous.mkdir(exist_ok=False);old={}
        for name in names+sidecars+pngs:
            output=adb_read(name)
            if output.returncode==0:
                path=previous/name;path.write_bytes(output.stdout);old[name]=sha(path)
            else:
                assert b'No such file or directory' in output.stderr+output.stdout,'Unknown pre-test output read failure'
        with (previous/'manifest.json').open('x',encoding='utf-8') as f:json.dump({'status':'PREEXISTING_TEST_OUTPUTS_NOT_CURRENT_ACCEPTANCE','sha256':old},f,indent=2)
        leaves=['files/'+n for n in names+sidecars+pngs];assert all(re.fullmatch(r'files/[A-Za-z0-9_.-]+\.(json|png)',n) for n in leaves)
        checks='set -eu; '+ '; '.join('test ! -L '+n for n in leaves)+'; rm -f '+' '.join(leaves)
        argv=[str(ADB),'-s','R3CT908DHHR','shell','run-as org.packrag.product sh -c '+shlex.quote(checks)]
        output=subprocess.run(argv,capture_output=True,timeout=30);assert output.returncode==0
        record['commands'].append({'label':cl+'-reset-exact-test-output-names','argv':argv,'returncode':output.returncode,'preexisting_sha256':old});save()
        command([sys.executable,'-X','utf8',str(HERE/'test_android_installed_0001.py'),'--serial','R3CT908DHHR','--build',str(build),'--run',str(current),'--class-name','org.packrag.product.'+cl,'--result-file',names[0],'--timeout','7200','--variant',variant],cl+'-instrumentation')
        manifest=read(current/'instrumentation-manifest.json');assert manifest['status']=='PASS' and manifest['transport']=='VERIFY_EXACT_INSTALLED_APKS_NO_REINSTALL'
        text=(current/'instrumentation.txt').read_text(encoding='utf-8');assert re.search(r'OK \('+str(entry['methods'])+r' tests?\)',text),cl
        expected={p.name:sha(p) for p in [build/('app-'+variant+'.apk'),build/('app-'+variant+'-androidTest.apk')]};assert manifest['apk_sha256']==expected
        assert manifest['selected_test_sources']['org.packrag.product.'+cl]['source_sha256']==entry['source_sha256']
        command([sys.executable,'-X','utf8','-m','scripts.v13_collect_phone_results','--run',str(current),'--files',','.join(names)],cl+'-collect')
        collection=read(current/'collected-results.json');assert set(collection['saved_sha256'])==set(names)
        for spec in entry['reports']:
            path=current/'original-adb'/spec['name'];assert sha(path)==collection['saved_sha256'][spec['name']];validate(read(path),spec)
        extras=current/'original-sidecars';extras.mkdir(exist_ok=False);extra={}
        for name in sidecars+pngs:
            output=adb_read(name);assert output.returncode==0,name
            if name.endswith('.png'):assert output.stdout.startswith(b'\x89PNG\r\n\x1a\n') and len(output.stdout)>1000,name
            path=extras/name;path.write_bytes(output.stdout);extra[name]=sha(path)
            if name.endswith('.png'):
                def declared_hashes(node):
                    if isinstance(node,dict):
                        if name in node and isinstance(node[name],dict) and 'sha256' in node[name]:yield node[name]['sha256']
                        if node.get('screenshot')==name and 'screenshot_sha256' in node:yield node['screenshot_sha256']
                        for item in node.values():yield from declared_hashes(item)
                    elif isinstance(node,list):
                        for item in node:yield from declared_hashes(item)
                declared=[value for spec in entry['reports'] for value in declared_hashes(read(current/'original-adb'/spec['name']))]
                for value in declared:assert value==extra[name],name+' declared screenshot hash mismatch'
        unchanged();command([sys.executable,'-X','utf8',str(HERE/'capture_owner_no_follow_0001.py'),'--output',args.prefix+'-'+cl.lower()+'-owner50.json'],cl+'-owner50')
        record['completed'].append({'class':cl,'methods':entry['methods'],'run':current.name,'original_sha256':collection['saved_sha256'],'sidecar_png_sha256':extra,'manifest_sha256':sha(current/'instrumentation-manifest.json')});save()
        print('ACCEPTED_NEW_ORIGINALS',cl,'methods',entry['methods'],flush=True)
        if is_ui and cl=='ProductAccessibilityUiTest':
            approval=HERE/(args.prefix+'-accessibility-visual-review.json')
            record.update(status='WAITING_REQUIRED_ORIGINAL_ACCESSIBILITY_PNG_REVIEW_NOT_ACCEPTANCE',required_visual_review=str(approval.name));save()
            stop=HERE/(args.prefix+'-stop-after-current.request');end=time.monotonic()+300
            while not approval.exists():
                if stop.exists() or time.monotonic()>=window['deadline_monotonic'] or time.monotonic()>=end:
                    record.update(status='HOLD_REQUIRED_ORIGINAL_PNG_REVIEW_NO_LATER_CLASS_STARTED',next_class=classes[classes.index(cl)+1] if classes.index(cl)+1<len(classes) else None);save();sys.exit(0)
                time.sleep(0.25)
            visual=read(approval);assert visual['status']=='PASS_MANUAL_FIVE_ORIGINAL_ACCESSIBILITY_PNGS_NOT_FULL_UI_ACCEPTANCE'
            assert visual['run']==current.name and visual['original_png_sha256']==extra
            record.update(status='RUNNING_CONSOLIDATED_PHASE_NOT_M4_ACCEPTANCE',accessibility_visual_review_sha256=sha(approval));save()
    guard('after');unchanged();record.update(status='PASS_FRESH_CONSOLIDATED_PHASE_NOT_FULL_M4_ACCEPTANCE',scope='Fixed selected per-class JUnit/count/ID contracts, exact current source/APK hashes, originals collected before next class, fresh output names and explicit owner50/source4 no-follow/mode guards. Private custody never enumerated. Native execution only where selected tests require it; no-INTERNET with mobile data on is not radio isolation. Synthetic signed protocol tests are not genuine calibration/domain gold, controlled performance or whole release acceptance. UI original PNG review remains independent.')
except Exception as failure:
    record.update(status='FAIL_HOLD_ALL_LATER_PHASES_NOT_ACCEPTANCE',failure_type=type(failure).__name__,failure_message=str(failure))
    if current is not None and current.exists():
        directory=current/'unaccepted-failure-originals';directory.mkdir(exist_ok=False);failure_hashes={}
        for name in names+sidecars+pngs:
            output=adb_read(name);path=directory/name;path.write_bytes(output.stdout);failure_hashes[name]={'sha256':sha(path),'returncode':output.returncode,'bytes':len(output.stdout),'scope':'Failure-time observation, not accepted current test result'}
        record['failure_observations']=failure_hashes
    raise
finally:
    record['updated_utc']=utc();save()
print(record['status'],flush=True)
