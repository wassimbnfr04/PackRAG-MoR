"""Save completed development custody and current policy progress without closing E3."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
M4 = ROOT / "artifacts/v1.3/m4"
target = HERE / "development-policy-transition.json"
assert not target.exists()

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

run = M4 / "device-diagnostics-full-0001"
manifest = read(run / "instrumentation-manifest.json")
saved = read(run / "collected-results.json")
execution = read(HERE / "full-background-execution.json")
assert manifest["status"] == saved["status"] == "PASS"
assert manifest["variant"] == "debug" and len(saved["saved_sha256"]) == 37
assert len(execution["commands"]) == 2 and all(row["returncode"] == 0 for row in execution["commands"])
for name, expected in saved["saved_sha256"].items():
    assert Path(name).name == name and Path(name).suffix == ".json"
    assert sha(run / "original-adb" / name) == expected
    assert read(run / name) == read(run / "original-adb" / name)
    assert read(run / name)["status"] == "PASS"
android = read(M4 / "build-0052/source-at-build-start.json")["files"]
assert android == read(M4 / "build-0053/source-at-build-start.json")["files"] and len(android) == 574
for name, expected in android.items():
    assert sha(ROOT / name) == expected, name
apks = {path.name: sha(path) for path in (M4 / "build-0052").glob("*.apk")}
assert manifest["apk_sha256"] == saved["apk_sha256"] == apks
text = (run / "instrumentation.txt").read_text(encoding="utf-8")
assert "OK (37 tests)" in text and "FAILURES" not in text
match = re.search(r"Time:\s*([0-9][0-9\s\u00a0\u202f]*[.,][0-9]+)", text)
assert match
seconds = float(re.sub(r"\s", "", match[1]).replace(",", "."))
policy_anchor = read(HERE / "policy-runner-observation.json")
value = dict(status="PASS_FULL37_ORIGINALS_POLICY30_RUNNING_NOT_E3_ACCEPTANCE",
    recorded_utc=datetime.now(timezone.utc).isoformat(), development_methods=37, development_originals=37,
    whole_development_instrumentation_seconds=seconds, source_inputs_unchanged=574, apk_sha256=apks,
    manifest_sha256=sha(run / "instrumentation-manifest.json"), collection_sha256=sha(run / "collected-results.json"),
    original_sha256=saved["saved_sha256"], policy_runner_observation_sha256=sha(HERE / "policy-runner-observation.json"),
    policy_observed_pid=policy_anchor["actual_observed_pid"],
    first_policy_progress_observation=dict(argv=[".venv-pack/Scripts/python.exe", "-X", "utf8", "artifacts/v1.3/m4/diagnostics-gate-0001/observe_policy_progress.py"],
        returncode=1, error="AssertionError: No single current product PID observed", output_file_created=False,
        limit="Initial observer refused before saving any progress. Its pid command return code/stdout were not retained by that exception, so absence versus multiple PIDs is not inferred. Later independent pidof returned7886/exit0; the succeeding unchanged observer bound the actual DiagnosticPolicyDeviceTest entry. This is an observational transition issue, not a product-test failure."),
    scope="Development37 and37 original results are complete; actual compiled-policy30 is running. Parity/restoration/closure/checkpoint remain required. No full E3/M4/product, held-out accuracy, performance or final-pack acceptance claimed.")
target.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
note = (f"E3 current {value['recorded_utc']}: actual development0052 full37 PASSES in{seconds}s, "
    "all37 original JSONs saved/hash-checked before switch;574 Android inputs unchanged. Compiled-policy0053 full30 is RUNNING under65092, "
    f"actual observed PID{policy_anchor['actual_observed_pid']}/DiagnosticPolicyDeviceTest entry. "
    "The first progress-only observer refused an unavailable single PID; unchanged retry observes the actual policy runner. "
    "No application failure or cause inferred from that observation. Finish policy/save30 originals, preserve old0014 pre-ADB path collision, "
    "fresh0015 restoration/originals, latest parity/check-only/closure/exact checkpoint before F. Mobile data remains on; USB connected/PackRAG closed during guards. "
    "Earlier failures and registry exception remain immutable. Functional time is not a benchmark.")
for name in ["STATUS.md", "PLAN.md"]:
    path = ROOT / name
    first, rest = path.read_text(encoding="utf-8-sig").split("\n", 1)
    path.write_text(first + "\n\n" + note + "\n\n" + rest, encoding="utf-8")
with (ROOT / "docs/v1.3/FULL_DOCUMENTATION_WORKING.md").open("a", encoding="utf-8") as stream:
    stream.write("\n\n" + note + "\n\nComplete command identities, original hashes and the observation issue are in diagnostics-gate-0001/development-policy-transition.json; frozen application inputs and all actual acceptance assertions remain unchanged.\n")
print(value["status"])
