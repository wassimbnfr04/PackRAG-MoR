"""Bounded TestRunner-only observation; not terminal acceptance or an application test."""
import argparse,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);args=parser.parse_args()
assert re.fullmatch(r'device-local-assets[a-z0-9-]*',args.run)
adb=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR'];commands=[]
def call(argv):
    result=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
    commands.append(dict(argv=argv,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr));return result
pid=call(adb+['shell','pidof','org.packrag.product']);values=pid.stdout.split()
if len(values)!=1 or not values[0].isdigit():
    print('No single current product PID; progress observation unavailable, no application failure inferred.');raise SystemExit(0)
out=call(adb+['logcat','-d','--pid='+values[0],'-v','threadtime','-s','TestRunner:I','*:S']);assert out.returncode==0
folder=HERE/'progress'/args.run;folder.mkdir(parents=True,exist_ok=True)
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');target=folder/(stamp+'.json');assert not target.exists()
target.write_text(json.dumps(dict(status='OBSERVATION_ONLY_NOT_TERMINAL_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    observed_pid=values[0],run_context=args.run,commands=commands,scope='Log rows belong to observed PID. Completed manifest/JUnit and originals, not this observation, establish test outcome.'),indent=2)+'\n',encoding='utf-8')
print('\n'.join(out.stdout.splitlines()[-8:]))
