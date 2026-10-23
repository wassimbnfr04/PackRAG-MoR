"""Bind the corrected F1 matched pair, public policy, host XML and tested bytes."""
import hashlib,json,subprocess,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'corrected-pair-preflight.json';assert not target.exists()
inputs=read(M4/'build-0056/source-at-build-start.json')['files']
assert inputs==read(M4/'build-0057/source-at-build-start.json')['files'] and len(inputs)==579
for name,value in inputs.items():assert sha(ROOT/name)==value,name
old=read(M4/'build-0055/source-at-build-start.json')['files']
delta={n:dict(before=old.get(n),after=v) for n,v in inputs.items() if old.get(n)!=v}
assert set(delta)=={'product/android/app/src/androidTest/java/org/packrag/product/LocalAssetReadinessDeviceTest.kt',
    'product/android/app/src/androidTest/java/org/packrag/product/LocalAssetsUiTest.kt'}
assert sha(M4/'build-0055/app-debug.apk')==sha(M4/'build-0056/app-debug.apk')
commands=[];apks={}
for name,variant in [('build-0056','debug'),('build-0057','demo')]:
    host=read(HERE/(name+'-host-capture.json'));assert host['host_totals']==dict(tests=62,failures=0,errors=0,skipped=0)
    assert host['variant']==variant
    apks[name]=host['apk_sha256']
    p=M4/name/('app-'+variant+'.apk');assert sha(p)==host['apk_sha256'][p.name]
    argv=[str(ROOT/'vendor/android-sdk/build-tools/37.0.0/aapt2.exe'),'dump','permissions',str(p)]
    output=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',errors='replace',check=True,timeout=30)
    assert 'android.permission.INTERNET' not in output.stdout
    commands.append(dict(argv=argv,returncode=output.returncode,stdout=output.stdout,stderr=output.stderr))
    with zipfile.ZipFile(p) as archive:
        assert archive.testzip() is None
        trust=archive.read('assets/release-trust.json');assert hashlib.sha256(trust).hexdigest()=='2bf01e87216790babca17fd0990731cf57a3877430a9662642a0f5e0d99c87a5'
record=dict(status='PASS_CORRECTED_F1_MATCHED_HOST_PAIR_NOT_DEVICE_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    android_inputs=579,host_methods_per_variant=62,two_test_only_changes_from_failed_0055=delta,
    unchanged_debug_product_from_0055_sha256=sha(M4/'build-0056/app-debug.apk'),apk_sha256=apks,commands=commands,
    scope='APK CRC/public trust pin/no INTERNET and matched source/host contracts. Original failed0055 device run remains FAIL; fresh physical tests required. Instrumentable demo is not final nondebuggable release acceptance.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
