"""Read-only current-PID log observation; no full acceptance inferred from progress."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
run=HERE/'development-progress-0001';run.mkdir(exist_ok=False)
command=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','logcat','-d','--pid=26484','-s','TestRunner:V','AndroidRuntime:E','*:S']
result=subprocess.run(command,capture_output=True,check=True);(run/'test-runner.log').write_bytes(result.stdout+result.stderr)
text=result.stdout.decode('utf-8');started=re.findall(r'I TestRunner: started: (.+)',text);finished=re.findall(r'I TestRunner: finished: (.+)',text)
failures=re.findall(r'E TestRunner: (.+)',text)
record=dict(status='RUNNING_COMPLETED_METHOD_LOG_OBSERVATION_NOT_FULL_GATE_OR_E1_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    run='device-query-regression-0001',actual_observed_pid=26484,command=command,started=started,finished=finished,errors_in_retained_log=failures,
    raw_log_sha256=hashlib.sha256(result.stdout+result.stderr).hexdigest(),
    limits='Read-only TestRunner progress; await final instrumentation PASS, original JSON collection and independent parity before closure. Phone log timestamps are device values, not host benchmark clocks.')
(run/'observation.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(status=record['status'],completed=len(finished),started=len(started),errors=len(failures))))
