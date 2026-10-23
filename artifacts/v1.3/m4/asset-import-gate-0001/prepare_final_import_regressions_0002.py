"""Version new final-source runners without altering historical runners or Android inputs."""
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
M4 = ROOT / 'artifacts/v1.3/m4'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

target = HERE / 'final-import-regression-preparation-0002.json'
assert not target.exists()
final = read(M4 / 'build-0076/source-at-build-start.json')['files']
assert len(final) == 599
assert all(sha(ROOT / name) == value for name, value in final.items())
prefix = 'product/android/app/src/'
names = [
    prefix + 'main/java/org/packrag/product/' + name + '.kt'
    for name in ['LocalAssetImporter', 'LocalAssetUriSource', 'LocalAssetLeases', 'ProductSession', 'PackRagViewModel']
]
names += [prefix + 'androidTest/java/org/packrag/product/' + name for name in [
    'AssetFixtureGrantReceiver.java', 'AssetFixtureProvider.java', 'LocalAssetImportTestSupport.kt',
    'LocalAssetImportFaultDeviceTest.kt', 'LocalAssetImportWalkingDeviceTest.kt',
    'LocalAssetImportProcessDeathDeviceTest.kt', 'LocalAssetImportAllSlotsDeviceTest.kt',
    'LocalAssetImportViewModelDeviceTest.kt',
]]
assert all(name in final for name in names)
differences = {}
for build in ['build-0063', 'build-0065', 'build-0066', 'build-0067', 'build-0070', 'build-0075']:
    previous = read(M4 / build / 'source-at-build-start.json')['files']
    differences[build] = {
        name: {'previous_sha256': previous.get(name), 'final_sha256': final[name]}
        for name in names if previous.get(name) != final[name]
    }

changes = {}
old_call = "[sys.executable,'-X','utf8','-m','scripts.v13_test_android'"
new_call = "[sys.executable,'-X','utf8',str(HERE/'test_android_installed_0001.py')"
for original, replacement in [
    ('run_hardening_0002.py', 'run_final_faults_installed_0001.py'),
    ('run_restart.py', 'run_final_restart_installed_0001.py'),
    ('run_all_slots.py', 'run_final_all_slots_installed_0001.py'),
    ('run_viewmodel.py', 'run_final_viewmodel_installed_0001.py'),
]:
    source = HERE / original
    destination = HERE / replacement
    assert not destination.exists()
    text = source.read_text(encoding='utf-8')
    assert text.count(old_call) == 1
    text = text.replace(old_call, new_call)
    text = text.replace("'--timeout','2400'", "'--timeout','3000'")
    # Existing semantic validators are preserved. Failed cat bytes are historical-style
    # failure captures only; these are never accepted as JSON or new PASS by the parent.
    ast.parse(text)
    destination.write_text(text, encoding='utf-8')
    changes[replacement] = dict(original=original, original_sha256=sha(source), prepared_sha256=sha(destination),
        changes='Installed-pair verification replaces reinstall; 2400s watchdog becomes 3000s where present. Deep validators unchanged; no performance acceptance.')

source = HERE / 'run_walking.py'
destination = HERE / 'run_final_walking_installed_0001.py'
assert not destination.exists()
text = source.read_text(encoding='utf-8')
old = """    for name in ['app-'+variant+'.apk','app-'+variant+'-androidTest.apk']:
        out=command([str(ADB),'-s',SERIAL,'install','-r',str(build/name)],180);assert b'Success' in out.stdout
"""
new = """    record['transport']='VERIFY_EXACT_INSTALLED_APKS_NO_REINSTALL'
    for package,name in zip(['org.packrag.product','org.packrag.product.test'],['app-'+variant+'.apk','app-'+variant+'-androidTest.apk']):
        out=command([str(ADB),'-s',SERIAL,'shell','pm','path',package])
        value=out.stdout.decode('utf-8').strip()
        assert re.fullmatch(r'package:/data/app/[A-Za-z0-9_./=+~-]+/base\\.apk',value),'Expected one installed public APK'
        out=command([str(ADB),'-s',SERIAL,'shell','sha256sum',value.removeprefix('package:')])
        assert out.stdout.decode('utf-8').split()[0]==host['apk_sha256'][name],'Installed pair mismatch; stop without reinstall'
"""
assert text.count(old) == 1
text = text.replace(old, new).replace("'org.packrag.product.test/androidx.test.runner.AndroidJUnitRunner'],1200)", "'org.packrag.product.test/androidx.test.runner.AndroidJUnitRunner'],3000)")
ast.parse(text)
destination.write_text(text, encoding='utf-8')
changes[destination.name] = dict(original=source.name, original_sha256=sha(source), prepared_sha256=sha(destination),
    changes='Two reinstall commands replaced by exact installed public APK SHA guards. Native watchdog1200s becomes3000s. Existing seven semantic controls, narrow grant, originals, owner50 before/after checks unchanged.')
assert all(sha(ROOT / name) == value for name, value in final.items())
record = dict(status='PREPARED_FINAL_SOURCE_IMPORT_REGRESSIONS_NOT_EXECUTED_OR_ACCEPTED',
    created_utc=datetime.now(timezone.utc).isoformat(), final_build='build-0076', final_android_inputs=599,
    selected_dependency_sha256={name: final[name] for name in names}, historical_dependency_differences=differences,
    prepared_runners=changes,
    scope='Explicit thirteen public dependency paths only; no directory/custody traversal. Historical outputs/runners immutable. Fresh final fault3methods/28controls, walking1/7, restart1/3, allslots1/8, ViewModel1/8 required. These are preparation only. Current adjacent batch remains frozen and uninterrupted. No radio/data/owner pack changes.')
target.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(record['status'])
