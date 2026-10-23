"""Exact public conflict/XML checkpoint whitelist after successful immutable closure."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
target=HERE/'checkpoint-files.json'
assert not target.exists()
gate=json.loads((HERE/'gate.json').read_text())
assert gate['status']=='M4C2B_CONFLICT_XML_VERIFIED_NOT_COMPLETE_M4_OR_PRODUCT'
files={**gate['output_sha256'],**gate['documents_at_closure']}
sources=[
 'product/packrag/conflicts.py','product/packrag/retrieval.py','product/packrag/prompt.py','product/packrag/runtime.py',
 'product/tests/test_conflicts.py','product/tests/test_conflict_integration.py','product/tests/test_prompt_serialization.py','product/tests/fixtures/conflict-contracts.json',
 'scripts/v13_conflict_fixtures.py','scripts/v13_conflict_smoke.py','scripts/v13_xml_prompt_fixtures.py',
 'product/android/core-model/src/main/java/org/packrag/model/Conflicts.kt','product/android/core-model/src/main/java/org/packrag/model/Contracts.kt','product/android/core-model/src/test/java/org/packrag/model/ConflictContractTest.kt',
 'product/android/retrieval/src/main/java/org/packrag/retrieval/Retrieval.kt',
 'product/android/grounded-runtime/src/main/java/org/packrag/runtime/PackRag.kt','product/android/grounded-runtime/src/main/java/org/packrag/runtime/Prompt.kt','product/android/grounded-runtime/src/test/java/org/packrag/runtime/OutputContractTest.kt',
 'product/android/app/src/androidTest/java/org/packrag/product/GeneratorPromptParityTest.kt',
 'product/android/app/src/androidTest/java/org/packrag/product/ConflictAssertions.kt','product/android/app/src/androidTest/java/org/packrag/product/ConflictDeviceTest.kt','product/android/app/src/androidTest/java/org/packrag/product/ConflictRuntimeDeviceTest.kt',
]
assets=ROOT/'product/android/app/src/androidTest/assets'
sources += [p.relative_to(ROOT).as_posix() for d in ['conflict-corpus','prompt-v13-xml-corpus'] for p in (assets/d).iterdir() if p.is_file()]
tested={**gate['source_sha256'],**gate['android_source_sha256']['build-0012']}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in sources:
 assert name in tested and sha(ROOT/name)==tested[name],name
 files[name]=tested[name]
for p in list(HERE.glob('*.py'))+[HERE/'gate.json',HERE/'PREPARATION_FAILURE.json']:
 files[p.relative_to(ROOT).as_posix()]=sha(p)
blocked={'temp','stage','pytest-temp','__pycache__','.private','build','.gradle','.cxx','.kotlin'}
for name,expected in files.items():
 path=ROOT/name
 assert path.resolve().is_relative_to(ROOT)
 # One explicit public builder stdout is retained; no other temp subtree enters.
 assert not blocked.intersection(Path(name).parts),name
 assert path.suffix.lower() not in {'.apk','.pyc','.class','.seed','.pem','.key','.keystore','.jks'},name
 assert sha(path)==expected,name
target.write_text(json.dumps(dict(purpose='EXPLICIT_CONFLICT_XML_CHECKPOINT_EXCLUDES_APKS_PRIVATE_WEIGHTS_TEMP_STAGE',files=dict(sorted(files.items()))),indent=2)+'\n')
print(json.dumps(dict(status='PASS',whitelist_files=len(files),manifest_itself_staged_separately=True)))
