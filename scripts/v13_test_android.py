"""Versioned instrumentation execution against explicitly selected new product APKs."""
import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from product.packrag.config import file_sha

ROOT = Path(__file__).resolve().parents[1]
ADB = ROOT / "vendor/platform-tools/adb.exe"

def build_apks(build: Path, variant: str):
    assert variant in ("debug", "demo"), "Unsupported instrumentation variant"
    result=json.loads((build/"build-result.json").read_text(encoding="utf-8-sig"))
    assert result["exit_code"]==0 and result.get("variant","debug")==variant, "Build artifact variant mismatch or failed build"
    paths=[build/("app-"+variant+".apk"),build/("app-"+variant+"-androidTest.apk")]
    assert all(path.is_file() for path in paths), "Selected variant APK pair missing"
    return paths


def selected_test_sources(build: Path, class_names: str):
    """Fail before ADB when selection is absent from the frozen build inputs."""
    identity = json.loads((build / "source-at-build-start.json").read_text(encoding="utf-8"))
    names = class_names.split(",")
    assert names and len(set(names)) == len(names), "Empty or duplicate test selection"
    selected = {}
    for name in names:
        assert re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)+", name), "Expected fully qualified test class"
        stem = "product/android/app/src/androidTest/java/" + name.replace(".", "/")
        paths = [stem + suffix for suffix in (".kt", ".java") if stem + suffix in identity["files"]]
        assert len(paths) == 1, "Test class not present in frozen build inputs: " + name
        selected[name] = dict(source=paths[0], source_sha256=identity["files"][paths[0]])
    return selected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    parser.add_argument("--build", required=True, type=Path)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--class-name", default="org.packrag.product.EmbeddingParityTest")
    parser.add_argument("--result-file", default="m2-embedding-parity.json")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--variant", choices=("debug","demo"), default="debug")
    args = parser.parse_args()
    args.run.mkdir(parents=True, exist_ok=False)
    record = dict(started_at=datetime.now(timezone.utc).isoformat(), serial=args.serial,
                  class_name=args.class_name, variant=args.variant, runner_sha256=file_sha(Path(__file__)),
                  commands=[])
    try:
        apks = build_apks(args.build,args.variant)
        record["apk_sha256"] = {path.name:file_sha(path) for path in apks}
        record["selected_test_sources"] = selected_test_sources(args.build, args.class_name)
        for path in apks:
            command = [str(ADB), "-s", args.serial, "install", "-r", str(path)]
            result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            record["commands"].append(dict(argv=command, returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
            assert result.returncode == 0 and "Success" in result.stdout, "Product APK installation failed"
        command = [str(ADB), "-s", args.serial, "shell", "am", "instrument", "-w", "-r", "-e", "class", args.class_name,
                   "org.packrag.product.test/androidx.test.runner.AndroidJUnitRunner"]
        output = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=args.timeout)
        (args.run / "instrumentation.txt").write_text(output.stdout + output.stderr, encoding="utf-8")
        print(output.stdout, flush=True)
        record["commands"].append(dict(argv=command, returncode=output.returncode))
        assert output.returncode == 0 and "OK (" in output.stdout and "FAILURES" not in output.stdout, "Instrumentation failed"
        command = [str(ADB), "-s", args.serial, "shell", "run-as", "org.packrag.product", "cat", "files/" + args.result_file]
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        assert result.returncode == 0, "Device structured result missing"
        device = json.loads(result.stdout)
        assert device["status"] == "PASS"
        (args.run / args.result_file).write_text(json.dumps(device, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        record["status"] = "PASS"
    except Exception:
        record["status"] = "FAIL"
        raise
    finally:
        (args.run / "instrumentation-manifest.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
