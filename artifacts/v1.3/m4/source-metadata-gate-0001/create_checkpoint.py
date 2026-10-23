"""Create an exact public checkpoint whitelist only after immutable gate closure."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
target = HERE / "checkpoint-files.json"
assert not target.exists(), "Checkpoint manifest is immutable"
gate = json.loads((HERE / "gate.json").read_text(encoding="utf-8"))
assert gate["status"] == "M4C2A_SOURCE_METADATA_VERIFIED_NOT_CONFLICT_RESOLUTION_OR_PRODUCT_COMPLETE"
files = dict(gate["output_sha256"])
files.update(gate["documents_at_closure"])
sources = [
    "product/packrag/packs.py", "product/packrag/runtime.py", "product/packrag/source_metadata.py",
    "product/tests/test_source_metadata.py", "scripts/v13_source_metadata_fixtures.py",
    "product/android/core-model/src/main/java/org/packrag/model/Contracts.kt",
    "product/android/core-model/src/main/java/org/packrag/model/RetrievalContracts.kt",
    "product/android/core-model/src/test/java/org/packrag/model/SourceMetadataTest.kt",
    "product/android/kpack-registry/src/main/java/org/packrag/packs/ActivePack.kt",
    "product/android/grounded-runtime/src/main/java/org/packrag/runtime/PackRag.kt",
    "product/android/app/src/androidTest/java/org/packrag/product/ProductRuntimeSmokeTest.kt",
    "product/android/app/src/androidTest/java/org/packrag/product/ReleaseTrustCoreDeviceTest.kt",
    "product/android/app/src/androidTest/java/org/packrag/product/SourceMetadataDeviceTest.kt",
]
sources += ["product/android/app/src/androidTest/assets/source-metadata-corpus/" + name
            for name in ("cases.json", "source-metadata.kpack", "public-key.raw")]
tested = {**gate["source_sha256"], **gate["android_source_sha256"]["build-0009"]}
for name in sources:
    assert name in tested and hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == tested[name], name
sources += [(HERE / name).relative_to(ROOT).as_posix()
            for name in ("gate.json", "collect_results.py", "create_checkpoint.py")]
for name in sources:
    files[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
blocked = {"temp", "stage", "pytest-temp", "__pycache__", ".private", "build", ".gradle", ".cxx", ".kotlin"}
for name, expected in files.items():
    path = ROOT / name
    assert path.resolve().is_relative_to(ROOT)
    assert not blocked.intersection(Path(name).parts), name
    assert path.suffix.lower() not in (".apk", ".pyc", ".class", ".seed", ".pem", ".key", ".keystore", ".jks"), name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
target.write_text(json.dumps(dict(purpose="EXPLICIT_SOURCE_METADATA_CHECKPOINT_EXCLUDES_APKS_PRIVATE_WEIGHTS_TEMP_STAGE",
    files=dict(sorted(files.items()))), indent=2) + "\n", encoding="utf-8")
print(json.dumps(dict(status="PASS", whitelist_files=len(files), manifest_itself_staged_separately=True)))
