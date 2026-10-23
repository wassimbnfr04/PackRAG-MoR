"""Real M1 smoke: owned pinned WSL server + ONNX + a newly signed developer pack.

Run with python -m scripts.v13_smoke --run artifacts/v1.3/m1/smoke-0001.
Never overwrites an existing run, historical pack, key, experiment or result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import time
import traceback
import urllib.error
import urllib.request
import zipfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from kpack_builder.core import PackError
from product.packrag.config import LOCK, file_sha, verify_file
from product.packrag.developer_pack import build
from product.packrag.embedding import GraniteEncoder
from product.packrag.generator import LlamaBackend
from product.packrag.packs import SessionRegistry, VerifiedPack
from product.packrag.retrieval import Query
from product.packrag.runtime import PackRAG
from scripts.v13_result_manifest import public_source_files

ROOT = Path(__file__).resolve().parents[1]
PORT = 18533
MODEL = ROOT / LOCK["generator"]["artifact"]
CANDIDATE = ROOT / "04_LFM25_26B_Candidate_Evidence"
BINARY = CANDIDATE / "runtime/wsl-build/bin/llama-server"
TEMPLATE = CANDIDATE / "model/chat_template.jinja"


def linux(path: Path) -> str:
    path = path.resolve()
    return "/mnt/" + path.drive[0].lower() + path.as_posix()[2:]


def save(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


@contextmanager
def owned_server(run: Path):
    verify_file(MODEL, LOCK["generator"]["sha256"])
    verify_file(BINARY, LOCK["generator"]["desktop_binary_sha256"])
    verify_file(TEMPLATE, LOCK["generator"]["chat_template_sha256"])
    http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        http.open(f"http://127.0.0.1:{PORT}/health", timeout=1).close()
    except (urllib.error.URLError, TimeoutError):
        pass
    else:
        raise RuntimeError("Smoke port is already in use; refuse to test or stop an unowned server")
    pidfile = run / "owned-server.pid"
    argv = [linux(BINARY), "-m", linux(MODEL), "-c", "2048", "-t", "8", "-tb", "8", "-ngl", "0",
            "-np", "1", "--host", "127.0.0.1", "--port", str(PORT), "--jinja",
            "--chat-template-file", linux(TEMPLATE), "--no-warmup", "--perf"]
    shell = "echo $$ > " + shlex.quote(linux(pidfile)) + "; exec " + shlex.join(argv)
    log = (run / "server.log").open("wb")
    started = time.perf_counter()
    process = subprocess.Popen(["wsl.exe", "-d", "kali-linux", "--exec", "bash", "-lc", shell],
                               stdout=log, stderr=subprocess.STDOUT)
    try:
        while time.perf_counter() - started < 180:
            if process.poll() is not None:
                raise RuntimeError("Owned llama server exited during startup; inspect server.log")
            try:
                with http.open(f"http://127.0.0.1:{PORT}/health", timeout=2) as response:
                    ready = json.load(response)
                if ready.get("status") == "ok":
                    break
            except (urllib.error.URLError, TimeoutError):
                pass
            time.sleep(.5)
        else:
            raise RuntimeError("Owned server readiness timeout")
        save(run / "server-identity.json", dict(argv=argv, distro="kali-linux", port=PORT,
                                                start_to_ready_host_ms=(time.perf_counter()-started)*1000,
                                                measurement="process start to health; not pure load or TTFT",
                                                model_sha256=file_sha(MODEL), binary_sha256=file_sha(BINARY),
                                                template_sha256=file_sha(TEMPLATE)))
        yield LlamaBackend(PORT, MODEL, TEMPLATE, BINARY)
    finally:
        if pidfile.exists():
            pid = int(pidfile.read_text(encoding="utf-8").strip())
            # Kill only this recorded process after verifying both executable and port.
            script = "import os,signal; p=" + str(pid) + "; c=open('/proc/%d/cmdline'%p,'rb').read(); "
            script += "assert " + repr(linux(BINARY).encode()) + " in c and " + repr(str(PORT).encode()) + " in c; os.kill(p,signal.SIGTERM)"
            stopped = subprocess.run(["wsl.exe", "-d", "kali-linux", "--exec", "python3", "-c", script],
                                     capture_output=True, text=True)
            save(run / "server-stop.json", dict(pid=pid, returncode=stopped.returncode,
                                                stdout=stopped.stdout, stderr=stopped.stderr))
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=10)
        log.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    run.mkdir(parents=True, exist_ok=False)
    status = "FAIL"
    results = []
    source_files = public_source_files(ROOT)
    save(run / "inputs.json", dict(started_at=datetime.now(timezone.utc).isoformat(),
                                   runtime_lock=LOCK, source_sha256={path.relative_to(ROOT).as_posix():file_sha(path) for path in source_files},
                                   historical_input_sha256=file_sha(ROOT / "gates/g0/g0_v1.jsonl")))
    try:
        encoder = GraniteEncoder(ROOT / "models/v1.3/granite")
        original = [json.loads(line) for line in (ROOT / "gates/g0/g0_v1.jsonl").read_text(encoding="utf-8").splitlines()][:10]
        names = ["Aster-9", "NexoFlow M4", "Helix-R", "QuantaGate Q7", "Meridia V3", "DeltaCell D2",
                 "Solace V2", "Orion-R12", "Vanta-P8", "Kestrel-K1"]
        cases = [dict(id=case["case_id"], title=name, aliases=[name], locator=case["case_id"], text=case["evidence"][0]["text"])
                 for case, name in zip(original, names, strict=True)]
        with owned_server(run) as generator:
            built = build(run / "developer-pack", cases, encoder, generator)
            with VerifiedPack(built["path"], [built["public_key"]], developer_mode=True) as pack:
                registry = SessionRegistry()
                runtime = PackRAG(registry, encoder, generator)
                absent = runtime.answer(Query("What is the Aster-9 temperature limit?", "2026-10-05"))
                assert absent["state"] == "NO_ACTIVE_PACK"
                results.append(dict(case_id="M1-NO-PACK", passed=True, result=absent))
                registry.activate(pack)
                # All ten historical direct facts are used as NEW integrated smoke inputs,
                # not counted as real-pack calibration or held-out PackBench questions.
                expected = ["74", "600", "LiFePO4", "three", "18", "20%", "8", "12", "80", "99.999%"]
                for case, fact in zip(original, expected, strict=True):
                    answer = runtime.answer(Query(case["question"], "2026-10-05"))
                    passed = answer["state"] == "ANSWER_ACCEPTED" and fact.casefold() in (answer["answer"] or "").casefold()
                    item = dict(case_id="M1-" + case["case_id"], passed=passed, expected_fact=fact, result=answer)
                    results.append(item)
                    save(run / (item["case_id"] + ".json"), item)
                    print(item["case_id"], answer["state"], "PASS" if passed else "FAIL", flush=True)
                    if not passed:
                        raise AssertionError("Real supported smoke failed: " + case["case_id"])
                for identity, question, state in [
                    ("M1-UNRELATED", "Who won the most recent football championship?", "NO_RELEVANT_EVIDENCE"),
                    ("M1-EXACT-NOT-SUFFICIENT", "What is the Aster-9 controller purchase price?", "INSUFFICIENT_EVIDENCE"),
                ]:
                    answer = runtime.answer(Query(question, "2026-10-05"))
                    passed = answer["state"] == state and answer["answer"] is None
                    item = dict(case_id=identity, passed=passed, expected_state=state, result=answer)
                    results.append(item)
                    save(run / (identity + ".json"), item)
                    print(identity, answer["state"], "PASS" if passed else "FAIL", flush=True)
                    assert passed, identity
                corrupt = run / "corrupt.kpack"
                with zipfile.ZipFile(built["path"]) as original_zip, zipfile.ZipFile(corrupt, "w") as output_zip:
                    for entry in original_zip.infolist():
                        payload = original_zip.read(entry.filename)
                        if entry.filename == "dense.kdx":
                            payload = payload[:-1] + bytes([payload[-1] ^ 1])
                        output_zip.writestr(entry, payload)
                try:
                    with VerifiedPack(corrupt, [built["public_key"]], developer_mode=True):
                        pass
                except PackError as error:
                    results.append(dict(case_id="M1-PAYLOAD-CORRUPTION", passed=True, error=str(error)))
                else:
                    raise AssertionError("Corrupted payload was activated")
        status = "PASS"
    except Exception:
        (run / "failure.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
    finally:
        save(run / "smoke-results.json", dict(status=status, cases=results,
                                             purpose="M1_REAL_DEVELOPMENT_E2E_NOT_RELEASE_OR_PACKBENCH",
                                             limitations=["Synthetic uncalibrated pack uses exact eligible aliases only for admission",
                                                          "Structural citations do not prove semantic support",
                                                          "Desktop WSL CPU, not Android or physical-device acceptance",
                                                          "No raw hidden reasoning persisted; final answers and actual token/timing metadata only"]))
        save(run / "output-hashes.json", {path.relative_to(run).as_posix():file_sha(path) for path in run.rglob("*")
                                         if path.is_file() and path.name != "output-hashes.json"})
    print("M1 real smoke PASS:", len(results), "cases", flush=True)


if __name__ == "__main__":
    main()
