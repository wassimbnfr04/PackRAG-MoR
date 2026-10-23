"""Read-only physical-device inventory; no radio, permission, thermal or kernel changes."""
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADB = ROOT / "vendor/platform-tools/adb.exe"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    args.run.mkdir(parents=True, exist_ok=False)
    commands = {
        "model": ["getprop", "ro.product.model"], "sdk": ["getprop", "ro.build.version.sdk"],
        "android": ["getprop", "ro.build.version.release"], "abi": ["getprop", "ro.product.cpu.abi"],
        "heap_growth_limit": ["getprop", "dalvik.vm.heapgrowthlimit"],
        "heap_maximum": ["getprop", "dalvik.vm.heapsize"],
        "cpu_online": ["cat", "/sys/devices/system/cpu/online"],
        "memory": ["cat", "/proc/meminfo"], "storage": ["df", "-h", "/data", "/sdcard"],
        "airplane_mode": ["settings", "get", "global", "airplane_mode_on"],
        "mobile_data": ["settings", "get", "global", "mobile_data"],
        "wifi_enabled": ["settings", "get", "global", "wifi_on"],
        "thermal_idle_inventory": ["dumpsys", "thermalservice"],
        "existing_lfm_sha256": ["sha256sum", "/data/local/tmp/packrag-lfm25-26b/model.gguf"],
    }
    result = dict(recorded_at=datetime.now(timezone.utc).isoformat(), serial=args.serial,
                  purpose="READ_ONLY_SETUP_INVENTORY_NOT_RUNTIME_PERFORMANCE", commands={})
    for name, command in commands.items():
        completed = subprocess.run([str(ADB), "-s", args.serial, "shell", *command], capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", timeout=30)
        result["commands"][name] = dict(argv=command, returncode=completed.returncode,
                                       stdout=completed.stdout, stderr=completed.stderr)
    (args.run / "phone-inventory.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Read-only inventory recorded; no phone settings changed.")


if __name__ == "__main__":
    main()
