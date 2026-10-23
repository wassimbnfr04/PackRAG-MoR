"""Two necessary real picker/lifecycle/control tests on the owned emulator."""
import hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];BUILD=ROOT/'artifacts/v1.3/m4/build-0113'
RUN=ROOT/'artifacts/v1.3/m4/emulator-chat-workflow-0003';RUN.mkdir(exist_ok=False)
ADB=ROOT/'vendor/platform-tools/adb.exe';SERIAL='emulator-5580'
record=dict(status='RUNNING_NOT_M4_ACCEPTANCE',started_utc=datetime.now(timezone.utc).isoformat(),serial=SERIAL,commands=[])
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save():(RUN/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
def adb(*args,timeout=180,check=True,binary=False):
    r=subprocess.run([str(ADB),'-s',SERIAL,*args],capture_output=True,timeout=timeout)
    record['commands'].append(dict(args=list(args),returncode=r.returncode,stdout='Saved binary original' if binary else r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace')));save()
    if check:assert r.returncode==0
    return r
inputs=json.loads((BUILD/'source-at-build-start.json').read_text())['files']
try:
    assert len(inputs)==631
    for name,digest in inputs.items():assert sha(ROOT/name)==digest,name
    assert adb('shell','getprop','ro.kernel.qemu').stdout.strip()==b'1'
    assert adb('shell','settings','get','system','font_scale').stdout.strip()==b'1.0'
    assert sha(BUILD/'app-debug.apk')==sha(ROOT/'artifacts/v1.3/m4/build-0106/app-debug.apk')
    record['apk_sha256']={p.name:sha(p) for p in [BUILD/'app-debug.apk',BUILD/'app-debug-androidTest.apk']}
    for p in record['apk_sha256']:assert b'Success' in adb('install','--no-streaming','-r',str(BUILD/p)).stdout
    result=adb('shell','am','instrument','-w','-r','-e','class','org.packrag.product.ChatWorkflowUiTest#largeFontLifecycleFiltersAndLocalAssetPicker',
        'org.packrag.product.test/androidx.test.runner.AndroidJUnitRunner',timeout=1500,check=False)
    (RUN/'instrumentation.txt').write_bytes(result.stdout);(RUN/'instrumentation.stderr.txt').write_bytes(result.stderr)
    originals=RUN/'original-adb';originals.mkdir();observed={}
    for name in ['m4-chat-workflow-controls.json']:
        raw=adb('exec-out','run-as','org.packrag.product','cat','files/'+name,check=False,binary=True)
        if raw.returncode!=0 or not raw.stdout.lstrip().startswith(b'{'):continue
        (originals/name).write_bytes(raw.stdout);value=json.loads(raw.stdout);observed[name]=value['status']
        assert value['controlled_file_count']==5 and len(value['owner_sha256'])==5
        for image,declared in value['visual_png'].items():
            assert image.endswith('.png') and '/' not in image and '\\' not in image
            path=originals/image;path.write_bytes(adb('exec-out','run-as','org.packrag.product','cat','files/'+image,binary=True).stdout)
            assert sha(path)==declared['sha256']
    record['observed_status']=observed;record['original_sha256']={p.name:sha(p) for p in originals.iterdir()}
    for name,digest in inputs.items():assert sha(ROOT/name)==digest,name
    assert result.returncode==0 and b'OK (1 test)' in result.stdout and b'FAILURES!!!' not in result.stdout
    assert len(observed)==1 and set(observed.values())=={'PASS'}
    record.update(status='PASS_EXECUTION_ORIGINAL_PNG_REVIEW_PENDING_NOT_M4',phone_touched=False)
except BaseException as e:record.update(status='FAIL_NO_WORKFLOW_ACCEPTANCE',error_type=type(e).__name__);raise
finally:record['updated_utc']=datetime.now(timezone.utc).isoformat();save()
print(record['status'],flush=True)
