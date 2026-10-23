"""Exact50 existing public owner files, no directory enumeration or private custody."""
import argparse,hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
target=HERE/args.output;assert target.parent==HERE and not target.exists() and target.suffix=='.json'
expected=json.loads((HERE/'before.json').read_text(encoding='utf-8'))['owner_public_file_sha256'];assert len(expected)==50
assert all(re.fullmatch(r'[A-Za-z0-9_.@/-]+',name) and '.private' not in Path(name).parts for name in expected)
argv=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell','run-as','org.packrag.product','sha256sum',*['files/'+name for name in sorted(expected)]]
start=datetime.now(timezone.utc).isoformat();out=subprocess.run(argv,capture_output=True,timeout=60);assert out.returncode==0
observed={}
for line in out.stdout.decode('utf-8').splitlines():
    value,name=line.split(maxsplit=1);assert re.fullmatch('[0-9a-f]{64}',value) and name.startswith('files/');observed[name[6:]]=value
record=dict(status='PASS_KNOWN50_EXISTING_PUBLIC_FILES_UNCHANGED' if observed==expected else 'FAIL_OWNER_FILE_CHANGE',started_utc=start,
    ended_utc=datetime.now(timezone.utc).isoformat(),owner_public_file_sha256=observed,
    command=dict(argv=argv,returncode=out.returncode,stdout=out.stdout.decode('utf-8'),stderr=out.stderr.decode('utf-8',errors='replace')),
    scope='50 explicit existing public paths only, no new full enumeration. Does not change/promote any failed prior attempt or establish native/UI acceptance.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');assert observed==expected;print(record['status'],flush=True)
