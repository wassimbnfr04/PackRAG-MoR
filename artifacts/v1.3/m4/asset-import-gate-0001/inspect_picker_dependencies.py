"""Public pinned dependency API inspection only; no Android input changes during phone gate."""
import hashlib,json,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
out=HERE/'picker-dependency-inspection-0001';out.mkdir(exist_ok=False)
aar=ROOT/'.cache/gradle/caches/modules-2/files-2.1/androidx.lifecycle/lifecycle-viewmodel-android/2.11.0/1ac7d4172a592c7b416f9bcd2b3724cdb0f4b0b3/lifecycle-viewmodel.aar'
jar=out/'lifecycle-2.11.0-classes.jar'
with zipfile.ZipFile(aar) as z:jar.write_bytes(z.read('classes.jar'))
jdk=json.loads((ROOT/'artifacts/week1/environment/android_tool_paths.json').read_text(encoding='utf-8-sig'))['jdk']
argv=[str(Path(jdk)/'bin/javap.exe'),'-classpath',str(jar),'androidx.lifecycle.ViewModelStore']
r=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',errors='replace',check=True,timeout=30)
(out/'viewmodel-store-api.txt').write_text(r.stdout+r.stderr,encoding='utf-8')
assert ' keys(' in r.stdout and ' put(' in r.stdout and ' get(' in r.stdout
record=dict(status='PASS_PINNED_PUBLIC_VIEWMODEL_STORE_API_INSPECTED_NOT_UI_ACCEPTANCE',dependency='androidx.lifecycle:lifecycle-viewmodel-android:2.11.0',
    classes_jar_sha256=hashlib.sha256(jar.read_bytes()).hexdigest(),argv=argv,returncode=r.returncode,
    scope='Pinned public dependency bytecode confirms keys/get/put for test-only actual-key lookup/replacement; library-group API harness only, no production use or guessed default key. Web androidx-main is background context, not claimed exact pinned binary.')
(out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(r.stdout)
