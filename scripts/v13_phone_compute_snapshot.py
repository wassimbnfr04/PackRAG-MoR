"""Read-only app CPU/scheduling/memory snapshot; no tuning or peak-memory claim."""
import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from product.packrag.config import file_sha

ROOT = Path(__file__).resolve().parents[1]
ADB = ROOT / "vendor/platform-tools/adb.exe"
PACKAGE = "org.packrag.product"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT) and not output.exists()
    base = [str(ADB), "-s", args.serial]
    def read(argv):
        result = subprocess.run(base + argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        return dict(argv=argv, returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
    pid = read(["shell", "pidof", PACKAGE])
    value = pid["stdout"].strip()
    assert re.fullmatch(r"\d+", value), "Exactly one current product process required"
    commands = [pid]
    for name in ("cgroup", "cpuset", "status", "stat", "sched"):
        commands.append(read(["shell", "run-as", PACKAGE, "cat", f"/proc/{value}/{name}"]))
    tasks = read(["shell", "run-as", PACKAGE, "ls", f"/proc/{value}/task"])
    commands.append(tasks)
    tids = [item for item in tasks["stdout"].split() if re.fullmatch(r"\d+", item)] if tasks["returncode"] == 0 else []
    assert len(tids) <= 128, "Unexpected thread count; bound diagnostics"
    with ThreadPoolExecutor(max_workers=4) as pool:
        thread_records = list(pool.map(lambda tid: read(["shell", "run-as", PACKAGE, "cat", f"/proc/{value}/task/{tid}/stat"]), tids))
    commands.extend(thread_records)
    threads = []
    for tid, record in zip(tids, thread_records, strict=True):
        if record["returncode"] != 0:
            continue
        suffix = record["stdout"].rsplit(") ", 1)[-1].split()
        if len(suffix) >= 37:
            threads.append(dict(tid=int(tid), user_ticks=int(suffix[11]), system_ticks=int(suffix[12]),
                                last_cpu=int(suffix[36]), state=suffix[0]))
    commands.append(read(["shell", "dumpsys", "meminfo", PACKAGE]))
    commands.append(read(["shell", "cat", "/proc/cpuinfo"]))
    for core in range(8):
        for name in ("scaling_cur_freq", "cpuinfo_max_freq", "scaling_governor"):
            commands.append(read(["shell", "cat", f"/sys/devices/system/cpu/cpu{core}/cpufreq/{name}"]))
    output.write_text(json.dumps(dict(recorded_utc=datetime.now(timezone.utc).isoformat(), serial=args.serial, pid=int(value),
        script_sha256=file_sha(Path(__file__)), purpose="READ_ONLY_SNAPSHOT_NOT_PEAK_OR_CAUSAL_BOTTLENECK_PROOF", threads=threads, commands=commands), indent=2) + "\n", encoding="utf-8")
    for record in commands[1:3]:
        print(record["argv"][-1], "rc=", record["returncode"], record["stdout"].strip(), flush=True)

if __name__ == "__main__":
    main()
