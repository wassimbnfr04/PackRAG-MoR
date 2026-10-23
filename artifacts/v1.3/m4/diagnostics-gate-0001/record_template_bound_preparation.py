"""Read-only public model-template metadata; not runtime or F acceptance."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
target = HERE / "template-bound-preparation.json"
assert not target.exists()
lock_path = ROOT / "product/config/toolchain.lock.json"
lock = json.loads(lock_path.read_text(encoding="utf-8-sig"))
prefix = [str(ROOT / "vendor/platform-tools/adb.exe"), "-s", "R3CT908DHHR", "shell", "run-as", "org.packrag.product"]
path = "files/models/chat_template.jinja"
commands = []
for tail in [["stat", "-c", "%s", path], ["sha256sum", path]]:
    argv = prefix + tail
    result = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=30, check=True)
    commands.append(dict(argv=argv, returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
size_text = commands[0]["stdout"].strip()
assert size_text.isdecimal()
size = int(size_text)
assert 0 < size <= 1024 * 1024
observed_hash = commands[1]["stdout"].split()[0]
assert observed_hash == lock["generator"]["chat_template_sha256"]
value = dict(
    status="READ_ONLY_PINNED_TEMPLATE_SIZE_PREPARATION_NOT_F_ACCEPTANCE",
    recorded_utc=datetime.now(timezone.utc).isoformat(),
    expected_sha256=lock["generator"]["chat_template_sha256"],
    observed_sha256=observed_hash,
    observed_bytes=size,
    public_lock_sha256=hashlib.sha256(lock_path.read_bytes()).hexdigest(),
    commands=commands,
    scope="Existing public runtime model-template artifact only. No private signing custody read, no model/registry/radio/APK/source mutation. Matching SHA256 binds this observed size to the existing pinned artifact; stat alone does not verify the other assets or establish F acceptance.",
)
target.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: value[key] for key in ["status", "observed_bytes", "observed_sha256"]}))
