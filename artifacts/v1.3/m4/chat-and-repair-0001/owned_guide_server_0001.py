from contextlib import contextmanager
from pathlib import Path
import urllib.request,urllib.error,json,time,shlex,subprocess
from scripts.v13_smoke import verify_file,LOCK,MODEL,BINARY,TEMPLATE,PORT,linux,file_sha,save,LlamaBackend
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
    argv = [linux(BINARY), "-m", linux(MODEL), "-c", "3072", "-t", "8", "-tb", "8", "-ngl", "0",
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
