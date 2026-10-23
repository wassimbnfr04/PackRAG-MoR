"""Record existing human instruction and actual phone readiness, no unlock action."""
import json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;ADB=ROOT/'vendor/platform-tools/adb.exe'
target=HERE/'foreground-retained-action-dispatch-readiness.json';assert not target.exists();commands=[]
for service in ['window','power']:
    args=[str(ADB),'-s','R3CT908DHHR','shell','dumpsys',service]+(['policy'] if service=='window' else [])
    out=subprocess.run(args,capture_output=True,check=True,timeout=30);value=out.stdout.decode('utf-8',errors='replace')
    lines=[line.strip() for line in value.splitlines() if (re.search(r'^\s*(showing|mIsShowing)=',line) if service=='window' else 'mWakefulness=' in line)]
    assert ('showing=false' in lines and 'mIsShowing=false' in lines) if service=='window' else 'mWakefulness=Awake' in lines
    commands.append(dict(argv=args,returncode=out.returncode,observed_readiness=lines))
target.write_text(json.dumps(dict(status='OWNER_CONTINUATION_AND_UNTOUCHED_INSTRUCTION_PHONE_AWAKE_UNLOCKED',
    recorded_utc=datetime.now(timezone.utc).isoformat(),owner_quote='Yes, retry after this run finishes; I will leave it untouched',
    source='Actual human async reply to question call_c24b849a9d95488f83378a9642057229, retained as current authorization for corrected two action-dispatch waits and announced new window; no new reply is invented.',
    foreground_window='About five minutes, announced immediately before the prepared test. Mobile data stays on.',
    commands=commands,scope='Readiness observed; no PIN/unlock/radio/governor/global-screen-timeout modification. Actual UI gate must independently pass.'),indent=2)+'\n',encoding='utf-8')
print('PASS existing owner authorization and current awake/unlocked phone')
