"""Capture a bounded product Android/build-script identity at test start."""
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from product.packrag.config import file_sha
from scripts.v13_result_manifest import public_path, public_tree_files

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT) and not output.exists()
    files = [path for path in public_tree_files(ROOT,"product/android") if path.name != "local.properties"]
    files += list((ROOT / "product/config").glob("*.json"))
    # Host tests consume shared protocol fixtures directly from the repository.
    # Include those bytes explicitly, even before an Android asset copy exists.
    files += [path for path in public_tree_files(ROOT,"product/tests") if path.suffix == ".json"]
    files += [ROOT / "kpack_builder/schema.sql"]
    files += [ROOT / "scripts/v13_build_android.ps1", ROOT / "scripts/v13_result_manifest.py", Path(__file__).resolve()]
    record = {"recorded_utc": datetime.now(timezone.utc).isoformat(), "scope": "ANDROID_PRODUCT_BUILD_CONFIG_SHARED_HOST_FIXTURES_AT_BUILD_START",
              "files": {str(path.relative_to(ROOT)).replace("\\", "/"): file_sha(path) for path in sorted(files)}}
    vendor = ROOT / "vendor/llama.cpp"
    git = ["git", "-c", "safe.directory=" + vendor.as_posix(), "-C", str(vendor)]
    commit = subprocess.check_output(git + ["rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(git + ["status", "--short"], text=True).strip()
    lock = json.loads((ROOT / "product/config/toolchain.lock.json").read_text(encoding="utf-8"))
    assert commit == lock["generator"]["llama_cpp_commit"] and not dirty, "Pinned native runtime must be clean"
    record["native_vendor"] = {"commit": commit, "working_tree_clean": not dirty}
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
