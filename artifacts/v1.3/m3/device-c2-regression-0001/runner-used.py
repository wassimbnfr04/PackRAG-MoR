"""Versioned instrumentation execution against explicitly selected new product APKs."""
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from product.packrag.config import file_sha

ROOT = Path(__file__).resolve().parents[1]
ADB = ROOT / "vendor/platform-tools/adb.exe"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    parser.add_argument("--build", required=True, type=Path)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--class-name", default="org.packrag.product.EmbeddingParityTest")
    parser.add_argument("--result-file", default="m2-embedding-parity.json")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    args.run.mkdir(parents=True, exist_ok=False)
    apks = [args.build / "app-debug.apk", args.build / "app-debug-androidTest.apk"]
    record = dict(started_at=datetime.now(timezone.utc).isoformat(), serial=args.serial,
                  class_name=args.class_name, apk_sha256={path.name:file_sha(path) for path in apks}, commands=[])
    try:
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
