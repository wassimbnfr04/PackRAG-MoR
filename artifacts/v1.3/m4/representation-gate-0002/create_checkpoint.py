"""Exact verified D2 public checkpoint; excludes APKs/weights/private custody."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
target=HERE/'checkpoint-files.json';assert not target.exists()
gate=json.loads((HERE/'gate.json').read_text());assert gate['status']=='M4D2_REPRESENTATIONS_VERIFIED_NOT_COMPLETE_D_M4_OR_PRODUCT'
files={**gate['output_sha256'],**gate['documents_at_closure']}
sources=['product/packrag/representations.py','product/packrag/packs.py','product/packrag/prompt.py','product/packrag/runtime.py',
    'product/tests/test_representations.py','product/tests/test_representation_integration.py','product/tests/test_prompt_serialization.py',
    'product/tests/fixtures/representation-contracts.json','scripts/v13_representation_fixtures.py','scripts/v13_representation_smoke.py','scripts/v13_android_source_identity.py',
    'product/android/core-model/src/main/java/org/packrag/model/GeneratorRepresentation.kt',
    'product/android/core-model/src/main/java/org/packrag/model/Contracts.kt',
    'product/android/core-model/src/test/java/org/packrag/model/GeneratorRepresentationTest.kt',
    'product/android/kpack-registry/src/main/java/org/packrag/packs/ActivePack.kt',
    'product/android/grounded-runtime/src/main/java/org/packrag/runtime/Prompt.kt',
    'product/android/grounded-runtime/src/main/java/org/packrag/runtime/PackRag.kt',
    'product/android/app/src/androidTest/java/org/packrag/product/RepresentationDeviceTest.kt']
sources += ['product/packrag/representations.py','product/tests/test_source_text.py','product/tests/fixtures/source-text-contracts.json','scripts/v13_source_text_fixtures.py','scripts/v13_source_text_smoke.py','product/android/core-model/src/main/java/org/packrag/model/SourceText.kt','product/android/core-model/src/main/java/org/packrag/model/QueryUnicode.kt','product/android/core-model/src/test/java/org/packrag/model/SourceTextTest.kt','product/android/kpack-registry/src/main/java/org/packrag/packs/DatabaseMetadata.kt','product/android/app/src/androidTest/java/org/packrag/product/SourceTextDeviceTest.kt']
sources += [p.relative_to(ROOT).as_posix() for p in (ROOT/'product/android/app/src/androidTest/assets/source-text-corpus').iterdir() if p.is_file()]
assets=ROOT/'product/android/app/src/androidTest/assets/representation-corpus'
sources += [p.relative_to(ROOT).as_posix() for p in assets.iterdir() if p.is_file()]
tested={**gate['source_sha256'],**gate['android_source_sha256']['build-0020']}
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
for name in sources:
    assert name in tested and digest(ROOT/name)==tested[name],name;files[name]=tested[name]
for path in [*HERE.glob('*.py'),*HERE.glob('*.json')]:files[path.relative_to(ROOT).as_posix()]=digest(path)
blocked={'temp','stage','pytest-temp','__pycache__','.private','build','.gradle','.cxx','.kotlin'}
for name,expected in files.items():
    path=ROOT/name;assert path.resolve().is_relative_to(ROOT) and not blocked.intersection(Path(name).parts),name
    assert path.suffix.lower() not in {'.apk','.pyc','.class','.seed','.pem','.key','.keystore','.jks','.gguf','.onnx','.safetensors'},name
    assert digest(path)==expected,name
target.write_text(json.dumps(dict(purpose='EXACT_D2_CHECKPOINT_NO_APK_PRIVATE_WEIGHTS_TEMP_CACHE',files=dict(sorted(files.items()))),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='PASS',whitelist_files=len(files),manifest_itself_staged_separately=True)))
