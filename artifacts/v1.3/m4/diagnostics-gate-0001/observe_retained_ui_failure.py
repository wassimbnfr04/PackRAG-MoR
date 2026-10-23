"""Read-only current readiness/app lifecycle evidence; never interrupt active instrumentation."""
import json,subprocess,re,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;ADB=ROOT/'vendor/platform-tools/adb.exe'
target=HERE/'retained-ui-initial-observation.json';assert not target.exists();commands=[]
for label,args,choose in [
    ('app-lifecycle',['logcat','-d','-s','ActivityTaskManager:I','ActivityManager:I','WindowManager:I'],lambda line:'packrag' in line.lower()),
    ('readiness-window',['shell','dumpsys','window','policy'],lambda line:bool(re.search(r'^\s*(showing|mIsShowing)=',line))),
    ('readiness-power',['shell','dumpsys','power'],lambda line:'mWakefulness=' in line),
    ('focus',['shell','dumpsys','window','windows'],lambda line:'mCurrentFocus=' in line or 'mFocusedApp=' in line),
    ('test-runner',['logcat','-d','-s','TestRunner:I'],lambda line:True)]:
    argv=[str(ADB),'-s','R3CT908DHHR']+args;result=subprocess.run(argv,capture_output=True,check=True,timeout=30)
    lines=[line for line in result.stdout.decode('utf-8',errors='replace').splitlines() if choose(line)]
    p=HERE/f'retained-ui-observed-{label}.txt';assert not p.exists();p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    commands.append(dict(argv=argv,returncode=result.returncode,saved=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
target.write_text(json.dumps(dict(status='OBSERVED_COMPOSE_HIERARCHY_LOSS_WHILE_SUITE_STILL_RUNNING_NOT_CAUSAL_DIAGNOSIS',
    recorded_utc=datetime.now(timezone.utc).isoformat(),commands=commands,
    scope='Read-only app-related lifecycle, current focus/readiness and original test logs. No screenshot edit, app restart, APK switch, wake/unlock/PIN/radio/global-timeout action. Let current suite finish and collect only truly completed fresh originals.'),indent=2)+'\n',encoding='utf-8')
print('Read-only lifecycle/readiness/failure evidence saved')
