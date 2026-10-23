"""Read only explicit retained test-UID source mode/type paths; no traversal or repair."""
import argparse,json,shlex,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
target=HERE/args.output;assert target.parent==HERE and target.suffix=='.json' and not target.exists()
namespace='files/f2-full-assets-0001'
expected={namespace:'500',namespace+'/owner.marker':'400',**{namespace+'/full-'+v+'.asset':'400' for v in ['generator','template','tokenizer','encoder']}}
script='set -eu; test -d files; test ! -L files; '
for path,mode in expected.items():
    script+='test ! -L '+path+'; test '+('-d' if path==namespace else '-f')+' '+path+'; '
script+='stat -c "%a %n" '+' '.join(expected)
avg=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell','run-as org.packrag.product.test sh -c '+shlex.quote(script)]
record=dict(started_utc=datetime.now(timezone.utc).isoformat(),scope='Exact six retained test-UID directory/marker/four source paths, no directory enumeration/content export/chmod/ownership mutation. Independent mode/type snapshot; sourceSHA proof is separate. Does not prove product model-file modes or performance.')
try:
    r=subprocess.run(avg,capture_output=True,text=True,encoding='utf-8',timeout=30);record['command']=dict(argv=avg,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr);assert r.returncode==0
    actual={line.split(maxsplit=1)[1]:line.split(maxsplit=1)[0] for line in r.stdout.splitlines()};record['observed_modes']=actual
    assert actual==expected;record['status']='PASS_EXPLICIT_SOURCE4_DIRECTORY_MARKER_MODES_TYPES_NOFOLLOW_SNAPSHOT'
except Exception as e:record.update(status='FAIL_SOURCE4_MODE_TYPE_SNAPSHOT_NO_REPAIR',failure_type=type(e).__name__,failure_message=str(e));raise
finally:record['ended_utc']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(record['status'])
