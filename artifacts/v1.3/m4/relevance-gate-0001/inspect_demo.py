"""Inspect packaged D1 demo; not final nondebuggable release acceptance."""
import hashlib,json,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
apk=ROOT/'artifacts/v1.3/m4/build-0015/app-demo.apk';out=ROOT/'artifacts/v1.3/m4/demo-apk-inspection-0008'
assert not out.exists();out.mkdir()
def sha(data):return hashlib.sha256(data).hexdigest()
permissions=subprocess.run([str(ROOT/'vendor/android-sdk/build-tools/37.0.0/aapt.exe'),'dump','permissions',str(apk)],check=True,capture_output=True).stdout
(out/'permissions.txt').write_bytes(permissions);assert b'android.permission.INTERNET' not in permissions
with zipfile.ZipFile(apk) as archive:
    names=archive.namelist();(out/'entries.txt').write_text('\n'.join(names)+'\n',encoding='utf-8')
    extensions=['.jks','.key','.keystore','.pem','.seed'];assert not any(Path(n).suffix.lower() in extensions for n in names)
    fixtures=['assets/development-public-key.raw','assets/lifecycle-public-key.raw','assets/developer-public-key.raw']
    namespaces=['conflict-corpus','prompt-v13-xml-corpus','relevance-corpus','relevance-reference-corpus']
    assert not set(fixtures).intersection(names)
    assert not any(n.startswith('assets/'+p+'/') for p in namespaces for n in names)
    store=archive.read('assets/release-trust.json');assert store==(ROOT/'product/config/release-trust.json').read_bytes()
    (out/'packaged-release-trust.json').write_bytes(store)
    native=sha(archive.read('lib/arm64-v8a/libpackrag_jni.so'))
    assert native=='361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef'
record=dict(status='PASS',purpose='PACKAGED_DEMO_POLICY_NOT_FINAL_NONDEBUGGABLE_RELEASE',apk_sha256=sha(apk.read_bytes()),no_internet=True,
    known_fixture_entries_checked_absent=fixtures+['assets/'+n+'/*' for n in namespaces],private_key_name_extensions_checked=extensions,
    approved_store_sha256=sha(store),native_sha256=native,limits=['Entry-name checks are not exhaustive byte-level secret scanning','Instrumentable Android Debug-signed demo, not final release/calibration acceptance'])
(out/'inspection.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record))
