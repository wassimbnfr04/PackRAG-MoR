"""Separate real-picker settled-image gate; preserve UI4 native acceptance and failed visuals."""
import argparse,hashlib,json,struct,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4';ADB=ROOT/'vendor/platform-tools/adb.exe'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);parser.add_argument('--run',required=True);parser.add_argument('--foreground-authorized',action='store_true',required=True);args=parser.parse_args()
run=M4/args.run;build=M4/args.build;target=HERE/(args.run+'-execution.json')
assert args.foreground_authorized and run.parent==M4 and build.parent==M4 and not run.exists() and not target.exists()
assert read(HERE/'visual-inspection-ui0004.json')['status'].startswith('FAIL_VISUAL_')
prior=read(HERE/'device-local-asset-import-ui-0004-execution.json');assert prior['status']=='PASS_F2_SYSTEM_PICKER_PHONE_CONTRACTS_VISUAL_REVIEW_PENDING_NOT_FULL_F2'
host=read(HERE/(args.build+'-capture.json'));assert host['status']=='PASS_F2_API_ITERATION_HOST_APK_CONTRACTS_NOT_DEVICE_OR_F2_ACCEPTANCE' and host['variant']=='debug'
sources=read(build/'source-at-build-start.json')['files'];accepted=read(M4/'build-0073/source-at-build-start.json')['files']
assert set(sources)-set(accepted)=={'product/android/app/src/androidTest/java/org/packrag/product/LocalAssetImportVisualDeviceTest.kt'}
assert all(sources.get(name)==value for name,value in accepted.items())
assert sha(build/'app-debug.apk')==sha(M4/'build-0073/app-debug.apk')
for name,value in sources.items():assert sha(ROOT/name)==value,name
files=['m4-local-asset-import-visual.json','m4-local-asset-import-visual-progress.json']
pngs=['m4-local-asset-import-visual-progress.png','m4-local-asset-import-visual-verified.png']
commands=[
    [sys.executable,'-X','utf8',str(HERE/'test_android_installed_0001.py'),'--serial','R3CT908DHHR','--build',str(build),'--run',str(run),'--class-name','org.packrag.product.LocalAssetImportVisualDeviceTest','--result-file',files[0],'--timeout','600','--variant','debug'],
    [sys.executable,'-X','utf8','-m','scripts.v13_collect_phone_results','--run',str(run),'--files',','.join(files)],
    [sys.executable,'-X','utf8',str(HERE/'prepare_full_sources.py'),'--build',args.build,'--output',args.run+'-after-source.json','--verify-only'],
    [sys.executable,'-X','utf8',str(HERE/'capture_known_guard.py'),'--output',args.run+'-after-known-guard.json']]
record=dict(status='RUNNING',started_utc=datetime.now(timezone.utc).isoformat(),runner_sha256=sha(Path(__file__)),build=args.build,run=args.run,foreground_authorized=True,unchanged_ui4_inputs=len(accepted),unchanged_product_apk_sha256=sha(build/'app-debug.apk'),commands=[])
try:
    for index,command in enumerate(commands):
        print(args.run,'stage',index,'START',flush=True)
        with (HERE/(args.run+f'-stage-{index}.stdout.txt')).open('xb') as out,(HERE/(args.run+f'-stage-{index}.stderr.txt')).open('xb') as err:result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
        record['commands'].append(dict(argv=command,returncode=result.returncode));target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        assert result.returncode==0,'Hold F2/F3; preserve and diagnose'
        if index==1:
            device=read(run/'original-adb'/files[0]);saved={}
            for name in pngs:
                result_png=subprocess.run([str(ADB),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/'+name],capture_output=True,timeout=30)
                payload=result_png.stdout;assert result_png.returncode==0 and payload.startswith(b'\x89PNG\r\n\x1a\n')
                path=run/'original-adb'/name;path.write_bytes(payload)
                assert sha(path)==device['visual_png'][name]['sha256'] and len(payload)==device['visual_png'][name]['bytes']
                frame=device['frame_observations'][name];assert struct.unpack('>II',payload[16:24])==(frame['width'],frame['height'])
                assert frame['equal_static_frames']>=3 and frame['samples']>=3 and frame['sample_interval_ms']==250 and frame['minimum_post_picker_wait_ms']==750
                saved[name]=sha(path)
            record['png_sha256']=saved
        print(args.run,'stage',index,'PASS',flush=True)
    device=read(run/'original-adb'/files[0]);collection=read(run/'collected-results.json')
    expected=['actual-picker-copy-settled-progress-and-cooperative-cancel','actual-picker-verified-template-settled-full-window','known-fifty-owner-public-files-unchanged']
    assert device['status']=='PASS' and device['variant']=='debug' and device['actual_weight_inference'] is False
    assert [case['id'] for case in device['cases']]==expected and all(case['passed'] is True for case in device['cases'])
    assert device['owner_registry_and_model_sha256']==read(HERE/'before.json')['owner_public_file_sha256'] and device['guards_unchanged'] is True
    for name in files:
        path=run/'original-adb'/name;value=read(path);assert sha(path)==collection['saved_sha256'][name]
        assert value['status']=='PASS' and value['test_id']==device['test_id'] and value['cases']==device['cases']
    for name,value in sources.items():assert sha(ROOT/name)==value,name
    record.update(status='PASS_F2_SEPARATE_PICKER_STATIC_FRAME_CONTRACTS_MANUAL_VISUAL_REVIEW_PENDING',original_sha256=collection['saved_sha256'],cases=expected,frame_observations=device['frame_observations'],
        scope='Separate actual template picker/progress/cancel/install experiment; exact unmodified PNGs sampled after static-content settling, counters/indicator and status/navigation margins excluded from settling fingerprint only. UI4 eight controls/native remain separately dated under exact unchanged598 sources and whole product APK. UI4 original visual FAIL unchanged. Independent visual review still required; no new native/performance/full F2/M4/product acceptance.')
except Exception as failure:
    record.update(status='FAIL',failure_type=type(failure).__name__,failure_message=str(failure))
    if run.exists():
        directory=run/'failure-original-adb';directory.mkdir(exist_ok=False);captures={}
        for name in files+pngs:
            result=subprocess.run([str(ADB),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/'+name],capture_output=True,timeout=30)
            path=directory/name;path.write_bytes(result.stdout)
            info=dict(returncode=result.returncode,sha256=sha(path),bytes=len(result.stdout),scope='Unaccepted failure-time bytes, possibly command error or stale; never promote to PASS')
            if name.endswith('.png'):info['valid_png_signature']=result.stdout.startswith(b'\x89PNG\r\n\x1a\n')
            else:
                try:
                    value=json.loads(result.stdout);info.update(valid_json=True,status=value.get('status'),test_id=value.get('test_id'))
                except (ValueError,UnicodeError):info['valid_json']=False
            captures[name]=info
        record['failure_captures']=captures
    raise
finally:
    record['finished_utc']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(record['status'],flush=True)
