"""Copy required final device JSON bytes before changing the installed APK variant."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

parser = argparse.ArgumentParser()
parser.add_argument("--run", required=True)
parser.add_argument("--prior-run", required=True)
args = parser.parse_args()
run = ROOT / "artifacts/v1.3/m4" / args.run
assert run.resolve().is_relative_to(ROOT / "artifacts/v1.3/m4")
manifest = json.loads((run / "instrumentation-manifest.json").read_text(encoding="utf-8"))
assert manifest["status"] == "PASS"
prior = json.loads((ROOT / "artifacts/v1.3/m4/source-metadata-gate-0001/gate.json").read_text(encoding="utf-8"))
names = prior["phone"][args.prior_run]["saved_results"] + ["m4-conflict-runtime.json"]
target = run / "collected-results.json"
assert not target.exists(), "Collection record is immutable"
saved = {}
payloads = {}
assert all(not (run / name).exists() for name in names), "Saved outputs cannot be overwritten"
for name in names:
    assert Path(name).name == name and name.endswith(".json")
    path = run / name
    assert not path.exists(), "Do not overwrite a saved result: " + name
    command = [str(ROOT / "vendor/platform-tools/adb.exe"), "-s", manifest["serial"],
               "shell", "run-as", "org.packrag.product", "cat", "files/" + name]
    result = subprocess.run(command, capture_output=True, timeout=30, check=True)
    parsed = json.loads(result.stdout)
    assert parsed["status"] == "PASS", name
    payloads[name] = result.stdout
    saved[name] = hashlib.sha256(result.stdout).hexdigest()
for name, payload in payloads.items():
    with (run / name).open("xb") as stream:
        stream.write(payload)
target.write_text(json.dumps(dict(status="PASS", recorded_utc=datetime.now(timezone.utc).isoformat(),
    serial=manifest["serial"], apk_sha256=manifest["apk_sha256"],
    source="App-private final JSON after complete successful instrumentation; original ADB bytes preserved",
    saved_sha256=saved), indent=2) + "\n", encoding="utf-8")
print(json.dumps(dict(status="PASS", run=args.run, saved=len(saved))))
