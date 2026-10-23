"""Read-only policy-stage progress; terminal JUnit and original JSONs decide acceptance."""
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
execution = json.loads((HERE / "full-background-execution.json").read_text(encoding="utf-8"))
assert len(execution["commands"]) >= 2
assert all(row["returncode"] == 0 for row in execution["commands"][:2])
assert (ROOT / "artifacts/v1.3/m4/device-diagnostics-policy-full-0001").is_dir()
prefix = [str(ROOT / "vendor/platform-tools/adb.exe"), "-s", "R3CT908DHHR"]
pid_argv = prefix + ["shell", "pidof", "org.packrag.product"]
pid_result = subprocess.run(pid_argv, capture_output=True, text=True, encoding="utf-8", timeout=30)
assert pid_result.returncode == 0 and re.fullmatch(r"[0-9]+", pid_result.stdout.strip()), "No single current product PID observed"
pid = int(pid_result.stdout.strip())
argv = prefix + ["logcat", "-d", "-s", "TestRunner:I"]
result = subprocess.run(argv, capture_output=True, check=True, timeout=30)
lines = [line for line in result.stdout.decode("utf-8", errors="replace").splitlines() if re.search(rf"\s{pid}\s", line)]
anchor = HERE / "policy-runner-observation.json"
if anchor.exists():
    assert json.loads(anchor.read_text(encoding="utf-8"))["actual_observed_pid"] == pid, "Current PID differs from observed policy runner"
else:
    starts = [line for line in lines if " I TestRunner: started: " in line and "org.packrag.product.DiagnosticPolicyDeviceTest)" in line]
    assert starts, "Policy runner entry not yet observed; do not count prior development logs"
    anchor.write_text(json.dumps(dict(status="FIRST_ACTUAL_POLICY_RUNNER_LOG_OBSERVED_NOT_ACCEPTANCE",
        recorded_utc=datetime.now(timezone.utc).isoformat(), actual_observed_pid=pid, first_policy_start=starts[0],
        pid_argv=pid_argv, pid_stdout=pid_result.stdout, log_argv=argv), indent=2) + "\n", encoding="utf-8")
folder = HERE / "policy-progress"
folder.mkdir(exist_ok=True)
index = 1
while (folder / f"{index:04d}.json").exists():
    index += 1
log = folder / f"{index:04d}.txt"
log.write_text("\n".join(lines) + "\n", encoding="utf-8")
finished, failed, latest = set(), set(), None
for saved in sorted(folder.glob("*.txt")):
    for line in saved.read_text(encoding="utf-8").splitlines():
        if " I TestRunner: finished: " in line:
            finished.add(line.split(" I TestRunner: finished: ", 1)[1])
        if " E TestRunner: failed: " in line:
            failed.add(line.split(" E TestRunner: failed: ", 1)[1])
        if " I TestRunner: started: " in line:
            latest = line.split(" I TestRunner: started: ", 1)[1]
value = dict(status="READ_ONLY_POLICY_PROGRESS_NOT_ACCEPTANCE", recorded_utc=datetime.now(timezone.utc).isoformat(),
    pid_argv=pid_argv, pid_stdout=pid_result.stdout, actual_observed_pid=pid, log_argv=argv,
    observed_log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(), cumulative_observed_finished_methods=len(finished),
    cumulative_observed_failed_methods=len(failed), latest_observed_method=latest,
    scope="Current package PID after completed development suite/original collection. Union of saved log observations is a lower bound; it is not full30 acceptance, gold accuracy or a performance benchmark. No APK/source/device mutation.")
(folder / f"{index:04d}.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: value[key] for key in ["recorded_utc", "actual_observed_pid", "cumulative_observed_finished_methods", "cumulative_observed_failed_methods", "latest_observed_method"]}))
