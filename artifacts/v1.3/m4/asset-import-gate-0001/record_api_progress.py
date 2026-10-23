"""Durable, explicitly partial F2 API iteration notes; never edits accepted F1 evidence."""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['started','finished'],required=True);parser.add_argument('--build',required=True);parser.add_argument('--run',required=True);args=parser.parse_args()
host=json.loads((HERE/(args.build+'-capture.json')).read_text(encoding='utf-8'))
assert host['status']=='PASS_F2_API_ITERATION_HOST_APK_CONTRACTS_NOT_DEVICE_OR_F2_ACCEPTANCE'
time=datetime.now(timezone.utc).isoformat()
if args.stage=='started':
    detail=f'F2 API walking test {args.run} is being started on {args.build}; no device PASS claimed yet.'
else:
    run=json.loads((M4/args.run/'execution.json').read_text(encoding='utf-8'))
    detail=f'F2 API walking test {args.run} terminal {run["status"]}; '
    detail+=('seven actual controls and saved original PASS; this iteration is not system-picker or complete F2 acceptance.' if run['status']=='PASS' else 'preserve failure and hold hardening/UI progression until diagnosed/repaired/revalidated.')
note=f'Current M4F2 at {time}: first build0058 FAIL at Kotlin compile because O_DIRECTORY is absent from public OsConstants; exact10 changed source inputs/build log and failed result preserved. Corrected directory sync opens O_RDONLY|O_NOFOLLOW|O_CLOEXEC, checks actual fstat descriptor S_ISDIR, then fsync/finally closes (existing registry pattern; no numeric hidden constant). {args.build} passes70 host methods (62 retained +8 new importer boundary methods), {host["android_inputs"]} frozen inputs/APK CRC/public trust/native pins/no product INTERNET. App unit task execution vs UP-TO-DATE modules is recorded in Gradle log. {detail} Caller models are closed before import; a foreign warm native reader must reject before provider opening. Test provider/grant receiver exist only in instrumentation APK and use an actual separate UID/narrow shell-DUMP-protected read grant, not the system picker. No owner model/partial/default-registry writes or radio changes are authorized. Keep PackRAG closed during background controls; a fresh foreground window will be announced for the later actual picker test. All-slot/fault/cancellation/restart/UI/policy/retained-adjacent/closure/exact checkpoint remain required before F3; F3/F4/later software/release/delivery remain. Owner supplies final knowledge packs.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
target=HERE/(args.run+'-'+args.stage+'-state.json');assert not target.exists()
target.write_text(json.dumps(dict(recorded_utc=time,stage=args.stage,build=args.build,run=args.run,note=note),indent=2)+'\n',encoding='utf-8');print(detail,flush=True)
