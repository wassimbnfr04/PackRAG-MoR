"""Read-only bounded development runner observations; not acceptance or benchmark."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
args=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','logcat','-d','-s','TestRunner:I']
result=subprocess.run(args,capture_output=True,check=True,timeout=30)
lines=[s for s in result.stdout.decode('utf-8',errors='replace').splitlines() if re.search(r'\s12346\s',s)]
folder=HERE/'development-progress';folder.mkdir(exist_ok=True)
n=1
while (folder/f'{n:04d}.json').exists():n+=1
log=folder/f'{n:04d}.txt';log.write_text('\n'.join(lines)+'\n',encoding='utf-8')
started=[s for s in lines if ' I TestRunner: started: ' in s];finished=[s for s in lines if ' I TestRunner: finished: ' in s];failed=[s for s in lines if ' E TestRunner: failed: ' in s]
value=dict(status='READ_ONLY_DEVELOPMENT_PROGRESS_NOT_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),argv=args,returncode=result.returncode,
    actual_main_test_pid=12346,latest_started=started[-1] if started else None,latest_finished=finished[-1] if finished else None,
    finished_methods_visible_in_current_log=len(finished),failed_methods_visible_in_current_log=len(failed),
    observed_log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),scope='Current retained log buffer only; dropped lines possible. Complete terminal JUnit/original result collection determines acceptance. No APK/source/device mutation.')
(folder/f'{n:04d}.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:value[k] for k in ['recorded_utc','latest_started','latest_finished','finished_methods_visible_in_current_log','failed_methods_visible_in_current_log']}))
