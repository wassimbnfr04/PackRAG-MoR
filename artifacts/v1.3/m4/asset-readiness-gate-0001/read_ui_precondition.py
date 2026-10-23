"""Record actual phone readiness before announcing the already authorized UI window."""
import argparse,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
parser=argparse.ArgumentParser();parser.add_argument('--attempt',required=True);args=parser.parse_args()
assert re.fullmatch(r'[0-9]{4}',args.attempt)
target=HERE/('ui-readiness-'+args.attempt+'.json');assert not target.exists()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
for name,phase in [('device-local-assets-0002','CORE'),('device-local-assets-adjacent-0002','ADJACENT')]:
    assert read(HERE/(name+'-verified.json'))['status']=='PASS_F1_'+phase+'_INDEPENDENT_ORIGINAL_CONTRACT_CHECK_NOT_CLOSURE'
commands=[];conditions=[]
for service in ['window','power']:
    argv=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell','dumpsys',service]+(['policy'] if service=='window' else [])
    result=subprocess.run(argv,capture_output=True,timeout=30)
    value=result.stdout.decode('utf-8',errors='replace')
    lines=[line.strip() for line in value.splitlines() if (re.search(r'^\s*(showing|mIsShowing)=',line) if service=='window' else 'mWakefulness=' in line)]
    commands.append(dict(argv=argv,returncode=result.returncode,observed=lines,stderr=result.stderr.decode('utf-8',errors='replace')))
    conditions.append(result.returncode==0 and (('showing=false' in lines and 'mIsShowing=false' in lines) if service=='window' else ('mWakefulness=Awake' in lines)))
passed=all(conditions)
record=dict(status='PASS_ACTUAL_AWAKE_UNLOCKED_PRECONDITION_NOT_UI_TEST_OR_ANNOUNCEMENT' if passed else 'FAIL_ACTUAL_UI_READINESS_NO_UI_TEST_STARTED',
    recorded_utc=datetime.now(timezone.utc).isoformat(),commands=commands,
    owner_quote='Yes, announce when it starts',scope='Read-only unlocked/awake observations. No activity launch, unlocking or radio modification. Announce the owner-authorized untouched window only after this PASS; run_ui independently rechecks before actual execution.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record,indent=2));raise SystemExit(0 if passed else 1)
