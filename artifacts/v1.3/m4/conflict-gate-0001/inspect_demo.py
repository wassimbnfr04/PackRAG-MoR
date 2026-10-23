"""Inspect actual packaged demo. Explicitly not final release acceptance."""
import hashlib,json,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
apk=ROOT/'artifacts/v1.3/m4/build-0013/app-demo.apk'
out=ROOT/'artifacts/v1.3/m4/demo-apk-inspection-0007'
assert not out.exists();out.mkdir()
def sha(data):return hashlib.sha256(data).hexdigest()
permissions=subprocess.run([str(ROOT/'vendor/android-sdk/build-tools/37.0.0/aapt.exe'),'dump','permissions',str(apk)],check=True,capture_output=True).stdout
(out/'permissions.txt').write_bytes(permissions)
assert b'android.permission.INTERNET' not in permissions
with zipfile.ZipFile(apk) as z:
 names=z.namelist();(out/'entries.txt').write_text('\n'.join(names)+'\n')
 private_extensions=['.jks','.key','.keystore','.pem','.seed']
 assert not any(Path(n).suffix.lower() in private_extensions for n in names)
 fixtures=['assets/development-public-key.raw','assets/lifecycle-public-key.raw','assets/developer-public-key.raw']
 assert not set(fixtures).intersection(names)
 assert not any(n.startswith('assets/conflict-corpus/') or n.startswith('assets/prompt-v13-xml-corpus/') for n in names)
 store=z.read('assets/release-trust.json');(out/'packaged-release-trust.json').write_bytes(store)
 assert store==(ROOT/'product/config/release-trust.json').read_bytes()
 native=sha(z.read('lib/arm64-v8a/libpackrag_jni.so'))
 assert native=='361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef'
record=dict(status='PASS',purpose='PACKAGED_DEMO_POLICY_NOT_FINAL_NONDEBUGGABLE_RELEASE',apk_sha256=sha(apk.read_bytes()),no_internet=True,known_fixture_entries_checked_absent=fixtures+['assets/conflict-corpus/*','assets/prompt-v13-xml-corpus/*'],private_key_name_extensions_checked=private_extensions,approved_store_sha256=sha(store),native_sha256=native,limits=['Entry-name checks are not exhaustive byte-level secret scanning','Instrumentable Android Debug-signed demo, not final release/calibration acceptance'])
(out/'inspection.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
