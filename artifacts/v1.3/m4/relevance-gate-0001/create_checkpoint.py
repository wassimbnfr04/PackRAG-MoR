"""Whitelist the verified D1 public source/evidence; exclude APKs/private/assets weights."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
target=HERE/'checkpoint-files.json';assert not target.exists()
gate=json.loads((HERE/'gate.json').read_text());assert gate['status']=='M4D1_RELEVANCE_FUSED_CAP_VERIFIED_NOT_COMPLETE_D_M4_OR_PRODUCT'
files={**gate['output_sha256'],**gate['documents_at_closure']}
sources=['product/packrag/relevance.py','product/packrag/retrieval.py','product/tests/test_relevance_gate.py',
    'product/tests/test_relevance_integration.py','product/tests/test_query_identifiers.py','product/tests/test_conflict_integration.py',
    'product/tests/fixtures/relevance-contracts.json','scripts/v13_relevance_references.py','scripts/v13_relevance_fixtures.py','scripts/v13_relevance_smoke.py',
    'product/android/core-model/src/main/java/org/packrag/model/RelevanceGate.kt','product/android/core-model/src/test/java/org/packrag/model/RelevanceGateTest.kt',
    'product/android/retrieval/src/main/java/org/packrag/retrieval/Retrieval.kt',
    'product/android/app/src/androidTest/java/org/packrag/product/QueryIdentifierDeviceTest.kt',
    'product/android/app/src/androidTest/java/org/packrag/product/ConflictDeviceTest.kt',
    'product/android/app/src/androidTest/java/org/packrag/product/RelevanceDeviceTest.kt']
assets=ROOT/'product/android/app/src/androidTest/assets'
sources += [p.relative_to(ROOT).as_posix() for namespace in ('relevance-corpus','relevance-reference-corpus') for p in (assets/namespace).iterdir() if p.is_file()]
tested={**gate['source_sha256'],**gate['android_source_sha256']['build-0014']}
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
for name in sources:
    assert name in tested and digest(ROOT/name)==tested[name],name
    files[name]=tested[name]
for path in [*HERE.glob('*.py'),*HERE.glob('*.json')]:files[path.relative_to(ROOT).as_posix()]=digest(path)
blocked={'temp','stage','pytest-temp','__pycache__','.private','build','.gradle','.cxx','.kotlin'}
for name,expected in files.items():
    path=ROOT/name;assert path.resolve().is_relative_to(ROOT) and not blocked.intersection(Path(name).parts),name
    assert path.suffix.lower() not in {'.apk','.pyc','.class','.seed','.pem','.key','.keystore','.jks'},name
    assert digest(path)==expected,name
target.write_text(json.dumps(dict(purpose='EXACT_D1_CHECKPOINT_NO_APK_PRIVATE_WEIGHTS_TEMP_CACHE',files=dict(sorted(files.items()))),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='PASS',whitelist_files=len(files),manifest_itself_staged_separately=True)))
