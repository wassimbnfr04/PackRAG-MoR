"""One real emulator UI method; exact APKs and original JSON/PNG evidence."""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BUILD=ROOT/'artifacts/v1.3/m4/build-0104'
RUN=ROOT/'artifacts/v1.3/m4/chat-walking-emulator-0002'
ADB=ROOT/'vendor/platform-tools/adb.exe'
SERIAL='emulator-5580'
assert not (HERE/'chat-ui-execution-0002.json').exists() and not RUN.exists()
record={'status':'RUNNING_NOT_UI_OR_M4_ACCEPTANCE','started_utc':datetime.now(timezone.utc).isoformat(),'serial':SERIAL,'commands':[]}
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save():
    (HERE/'chat-ui-execution-0002.json').write_text(json.dumps(record,indent=2)+'\n')
def adb(*args):
    argv=[str(ADB),'-s',SERIAL,*args]
    r=subprocess.run(argv,capture_output=True,timeout=180)
    record['commands'].append({'argv':argv,'returncode':r.returncode,'stdout':r.stdout.decode('utf-8',errors='replace') if args[0]!='exec-out' else 'Binary/original output saved separately','stderr':r.stderr.decode('utf-8',errors='replace')})
    save();assert r.returncode==0
    return r.stdout
try:
    assert adb('shell','getprop','ro.kernel.qemu').strip()==b'1'
    assert adb('shell','getprop','sys.boot_completed').strip()==b'1'
    record['supported_abis']=adb('shell','getprop','ro.product.cpu.abilist').decode().strip()
    assert 'arm64-v8a' in record['supported_abis']
    assert adb('shell','settings','get','system','font_scale').strip()==b'1.0'
    inputs=json.loads((BUILD/'source-at-build-start.json').read_text())['files']
    assert len(inputs)==629
    for name,value in inputs.items():assert sha(ROOT/name)==value,name
    product=BUILD/'app-debug.apk'
    assert sha(product)!=sha(ROOT/'artifacts/v1.3/m4/build-0097/app-debug.apk'),'Chat product change must be identified as new APK'
    record['product_unchanged_from_phone_build0097']=False
    record['apk_sha256']={p.name:sha(p) for p in [product,BUILD/'app-debug-androidTest.apk']}
    for apk in [product,BUILD/'app-debug-androidTest.apk']:
        result=adb('install','--no-streaming','-r',str(apk))
        assert b'Success' in result
    helper=ROOT/'artifacts/v1.3/m4/consolidated-f3-f4-0001/test_android_installed_0001.py'
    command=[sys.executable,'-X','utf8',str(helper),'--serial',SERIAL,'--build',str(BUILD),'--run',str(RUN),'--class-name','org.packrag.product.ChatWalkingUiTest','--result-file','m4-chat-walking.json','--timeout','900']
    r=subprocess.run(command,cwd=ROOT,capture_output=True)
    (HERE/'chat-ui-0002.stdout.txt').write_bytes(r.stdout);(HERE/'chat-ui-0002.stderr.txt').write_bytes(r.stderr)
    record['commands'].append({'argv':command,'returncode':r.returncode});save()
    assert r.returncode==0
    manifest=json.loads((RUN/'instrumentation-manifest.json').read_text())
    assert manifest['status']=='PASS' and manifest['apk_sha256']==record['apk_sha256']
    assert 'OK (1 test)' in (RUN/'instrumentation.txt').read_text()
    original=RUN/'original-adb';original.mkdir(exist_ok=False)
    raw=adb('exec-out','run-as','org.packrag.product','cat','files/m4-chat-walking.json')
    path=original/'m4-chat-walking.json';path.write_bytes(raw)
    value=json.loads(raw);assert value['status']=='PASS' and value['actual_weight_inference'] is False
    assert len(value['cases'])==4 and value['environment']=='FRESH_EMULATOR'
    hashes={path.name:sha(path)}
    expected={'m4-chat-normal-empty.png','m4-chat-two-turns.png','m4-chat-large-font-composer.png','m4-chat-large-font-controls.png'}
    assert set(value['visual_png'])==expected
    for name in sorted(expected):
        raw=adb('exec-out','run-as','org.packrag.product','cat','files/'+name)
        assert raw.startswith(b'\x89PNG\r\n\x1a\n') and len(raw)>1000
        path=original/name;path.write_bytes(raw);hashes[name]=sha(path)
        assert hashes[name]==value['visual_png'][name]['sha256']
    for name,hash_value in inputs.items():assert sha(ROOT/name)==hash_value,name
    record.update(status='PASS_CHAT_WALKING_METHOD_FOUR_CONTROLS_ORIGINAL_PNG_REVIEW_REQUIRED',original_sha256=hashes,scope='Actual new chat product APK, real emulator Activity/ViewModel no-pack path. No fake generator, no repair capability or physical performance claim; full M4 remains pending.')
except Exception as exc:
    record.update(status='FAIL_NO_UI_ACCEPTANCE',error=str(exc))
    raise
finally:
    record['updated_utc']=datetime.now(timezone.utc).isoformat();save()
print(record['status'],flush=True)
