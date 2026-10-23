"""Install hash-pinned model data into the debug app's private files as its own UID."""
import argparse
import json
import subprocess
import time
from pathlib import Path

from product.packrag.config import LOCK, file_sha

ROOT = Path(__file__).resolve().parents[1]
ADB = ROOT / "vendor/platform-tools/adb.exe"
PACKAGE = "org.packrag.product"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--include-generator", action="store_true")
    args = parser.parse_args()
    args.run.mkdir(parents=True, exist_ok=False)
    base = [str(ADB), "-s", args.serial, "shell", "-T", "-e", "none", "run-as", PACKAGE]
    assets = [(ROOT / "models/v1.3/granite" / name, "files/models/granite/" + name,
               LOCK["embedder"]["asset_sha256"][name]) for name in ("tokenizer.json", "onnx/model.onnx")]
    if args.include_generator:
        assets.append((ROOT / LOCK["generator"]["artifact"], "files/models/" + LOCK["generator"]["artifact"], LOCK["generator"]["sha256"]))
        assets.append((ROOT / "04_LFM25_26B_Candidate_Evidence/model/chat_template.jinja", "files/models/chat_template.jinja", LOCK["generator"]["chat_template_sha256"]))
    records = []
    status = "FAIL"
    try:
        for source, destination, expected in assets:
            assert file_sha(source) == expected
            command = base + ["mkdir", "-p", str(Path(destination).parent).replace("\\", "/")]
            subprocess.run(command, check=True, capture_output=True)
            existing = subprocess.run(base + ["sha256sum", destination], capture_output=True, text=True)
            if existing.returncode == 0:
                assert existing.stdout.split()[0] == expected, "Existing app asset differs; refuse silent overwrite"
                subprocess.run(base + ["chmod", "600", destination], check=True, capture_output=True)
                records.append(dict(path=destination, sha256=expected, acquisition="EXISTING_VERIFIED_PRIVATE_ASSET"))
                continue
            partial = destination + ".part-" + args.run.name
            # Windows adb shell stdin uses text mode and stops at Ctrl-Z; exec-in
            # selects the binary transport. Do not use a text shell pipeline for assets.
            command = [str(ADB), "-s", args.serial, "exec-in", "run-as", PACKAGE,
                       "dd", "of=" + partial, "bs=65536"]
            with source.open("rb") as stream:
                result = subprocess.run(command, stdin=stream, capture_output=True, timeout=900)
            assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
            # exec-in can return before the remote tiny-file writer has completed.
            # Acceptance remains the full expected SHA, with a bounded completion wait.
            attempts = []
            for attempt in range(50):
                digest = subprocess.run(base + ["sha256sum", partial], capture_output=True, text=True)
                attempts.append(dict(returncode=digest.returncode, stdout=digest.stdout, stderr=digest.stderr))
                if digest.returncode == 0 and digest.stdout.split()[0] == expected:
                    break
                time.sleep(.2)
            else:
                records.append(dict(path=partial, status="TRANSPORT_HASH_NOT_ACCEPTED", attempts=attempts))
                raise AssertionError("Private asset transport hash mismatch or remote completion timeout")
            subprocess.run(base + ["chmod", "600", partial], check=True, capture_output=True)
            subprocess.run(base + ["mv", partial, destination], check=True, capture_output=True)
            records.append(dict(path=destination, bytes=source.stat().st_size, sha256=expected,
                                acquisition="BINARY_ADB_EXEC_IN_DD_APP_UID_HASH_VERIFIED_THEN_RENAMED", hash_completion_attempts=attempts,
                                transport_returncode=result.returncode, transport_stderr=result.stderr.decode("utf-8", errors="replace")))
            print("Private asset installed and verified:", destination, flush=True)
        status = "PASS"
    finally:
        (args.run / "private-assets.json").write_text(json.dumps(dict(status=status, serial=args.serial, package=PACKAGE, files=records), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
