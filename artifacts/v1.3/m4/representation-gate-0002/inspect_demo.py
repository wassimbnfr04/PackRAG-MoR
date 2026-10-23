"""Inspect packaged policy APK public entries; never read private key custody."""
import hashlib,json,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];M4=ROOT/'artifacts/v1.3/m4'
run=M4/'demo-apk-inspection-0010';run.mkdir(exist_ok=False)
apk=M4/'build-0021/app-demo.apk'
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
aapt=ROOT/'vendor/android-sdk/build-tools/37.0.0/aapt2.exe'
commands=[]
for mode in ('permissions','badging'):
    args=[str(aapt),'dump',mode,str(apk)];result=subprocess.run(args,capture_output=True,check=True)
    (run/(mode+'.txt')).write_bytes(result.stdout+result.stderr);commands.append(dict(argv=args,returncode=result.returncode))
permissions=(run/'permissions.txt').read_text();badging=(run/'badging.txt').read_text()
assert 'android.permission.INTERNET' not in permissions and 'application-debuggable' in badging
private_extensions={'.jks','.key','.keystore','.pem','.seed'}
known=['assets/development-public-key.raw','assets/lifecycle-public-key.raw','assets/developer-public-key.raw']
namespaces=['conflict-corpus','prompt-v13-xml-corpus','relevance-corpus','relevance-reference-corpus','representation-corpus','source-text-corpus']
with zipfile.ZipFile(apk) as archive:
    entries=sorted(archive.namelist());(run/'entries.txt').write_text('\n'.join(entries)+'\n')
    assert not set(known).intersection(entries)
    assert not any(Path(e).suffix.lower() in private_extensions for e in entries)
    assert not any(e.startswith('assets/'+namespace+'/') for e in entries for namespace in namespaces)
    store=archive.read('assets/release-trust.json');(run/'packaged-release-trust.json').write_bytes(store)
    store_hash=hashlib.sha256(store).hexdigest();assert store_hash==digest(ROOT/'product/config/release-trust.json')
    native_hash=hashlib.sha256(archive.read('lib/arm64-v8a/libpackrag_jni.so')).hexdigest()
    assert native_hash=='361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef'
record=dict(status='PASS',purpose='PACKAGED_DEMO_POLICY_NOT_FINAL_NONDEBUGGABLE_RELEASE',apk_sha256=digest(apk),no_internet=True,
    known_fixture_entries_checked_absent=known+['assets/'+n+'/*' for n in namespaces],private_key_name_extensions_checked=sorted(private_extensions),
    approved_store_sha256=store_hash,native_sha256=native_hash,commands=commands,
    limits=['Entry-name checks are not exhaustive byte-level secret scanning','Debuggable policy demo configured with Android Debug signing; not final release/calibration acceptance'])
(run/'inspection.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record))
