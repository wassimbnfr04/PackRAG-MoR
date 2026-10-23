"""Prepare exact unchanged-product phone fallback; do not start foreground tests."""
import json,hashlib,subprocess,uuid
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
BUILD=ROOT/'artifacts/v1.3/m4/build-0110';OUT=HERE/'phone-repair-preparation-0002.json';assert not OUT.exists()
ADB=ROOT/'vendor/platform-tools/adb.exe';SERIAL='R3CT908DHHR'
record=dict(status='PREPARING_NO_TEST_LAUNCHED',serial=SERIAL,started_utc=datetime.now(timezone.utc).isoformat(),commands=[])
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save():OUT.write_text(json.dumps(record,indent=2)+'\n')
def adb(*args,timeout=180):
    r=subprocess.run([str(ADB),'-s',SERIAL,*args],capture_output=True,timeout=timeout)
    record['commands'].append(dict(args=list(args),returncode=r.returncode,stdout=r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace')));save()
    assert r.returncode==0;return r.stdout.decode().strip()
try:
    assert adb('get-state')=='device';assert adb('shell','getprop','ro.kernel.qemu')!='1'
    record['device']={p:adb('shell','getprop',p) for p in ['ro.product.model','ro.product.manufacturer','ro.build.version.release','ro.product.cpu.abilist']}
    assert record['device']['ro.product.manufacturer'].lower()=='samsung'
    inputs=json.loads((BUILD/'source-at-build-start.json').read_text())['files'];assert len(inputs)==630
    for name,value in inputs.items():assert sha(ROOT/name)==value,name
    assert sha(BUILD/'app-debug.apk')==sha(ROOT/'artifacts/v1.3/m4/build-0106/app-debug.apk')
    record['apk_sha256']={p.name:sha(p) for p in [BUILD/'app-debug.apk',BUILD/'app-debug-androidTest.apk']}
    record['reused_previously_installed_apks']=True
    for package,filename in [('org.packrag.product','app-debug.apk'),('org.packrag.product.test','app-debug-androidTest.apk')]:
        installed=adb('shell','pm','path',package).removeprefix('package:')
        assert installed.startswith('/data/app/') and installed.endswith('/base.apk') and '\n' not in installed
        assert adb('shell','sha256sum',installed).split()[0]==record['apk_sha256'][filename]
    pack=ROOT/'artifacts/v1.3/m4/repair-skills-prepared-0001/repair-skills.kpack'
    assert sha(pack)=='c202956eb0554fecc439944ebf4d69b831ad4fa262ea1693d4ec7f00e0952359'
    destination='files/m4-repair-fixture-0001.kpack';adb('shell','run-as','org.packrag.product','test','!','-e',destination)
    staging='/data/local/tmp/packrag-m4-repair-'+str(uuid.uuid4())+'.kpack';record['staging']=staging
    adb('shell','test','!','-e',staging);adb('push',str(pack),staging);adb('shell','chmod','644',staging)
    adb('shell','run-as','org.packrag.product','cp',staging,destination);adb('shell','run-as','org.packrag.product','chmod','400',destination)
    assert adb('shell','run-as','org.packrag.product','sha256sum',destination).split()[0]==sha(pack)
    assert adb('shell','run-as','org.packrag.product','stat','-c','%a',destination)=='400'
    adb('shell','rm',staging)
    record.update(status='PASS_PREPARED_EXACT_APKS_FROZEN_TEST_PACK_NO_TEST_LAUNCHED',product_same_as_build0106=True,
        phone_settings_changed=False,model_weights_transferred=False,fixture_sha256=sha(pack),completed_utc=datetime.now(timezone.utc).isoformat());save()
except BaseException as e:record.update(status='FAILED_NO_TEST_LAUNCHED',error_type=type(e).__name__);save();raise
print(record['status'],flush=True)
