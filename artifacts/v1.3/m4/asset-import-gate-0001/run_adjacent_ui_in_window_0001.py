"""Launch one UI class only inside an explicitly recorded human foreground window."""
import argparse,hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
parser=argparse.ArgumentParser();parser.add_argument('--selection',choices=['management','query','sources','diagnostics','assets'],required=True)
parser.add_argument('--run',required=True);parser.add_argument('--build',required=True);parser.add_argument('--window-proof',default='adjacent-ui-window-start-0001.json');args=parser.parse_args()
assert re.fullmatch(r'device-local-asset-adjacent-ui-[a-z0-9-]+',args.run)
window_path=HERE/args.window_proof;assert window_path.parent==HERE and window_path.suffix=='.json'
window=json.loads(window_path.read_text(encoding='utf-8-sig'));assert window['status']=='AUTHORIZED_ANNOUNCED_UI_WINDOW_STARTED_NOT_TEST_ACCEPTANCE'
assert window['build']==args.build and args.selection in window['selections']
now=datetime.now(timezone.utc);remaining=(datetime.fromisoformat(window['launch_deadline_utc'])-now).total_seconds()
assert remaining>10,'Foreground launch deadline reached; no class starts without renewed explicit human window'
target=HERE/(args.run+'-window-launch.json');assert not target.exists()
record=dict(status='AUTHORIZED_CLASS_LAUNCH_NOT_TEST_ACCEPTANCE',selection=args.selection,started_utc=now.isoformat(),remaining_window_seconds_at_launch=remaining,
    window_proof_sha256=hashlib.sha256(window_path.read_bytes()).hexdigest(),scope='Only new class launch is gated; a running class may finish after deadline. This is not test/visual PASS. Mobile data on, no reinstalls.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
argv=[sys.executable,'-X','utf8',str(HERE/'run_adjacent_ui.py'),'--build',args.build,'--run',args.run,'--selection',args.selection,'--foreground-authorized']
result=subprocess.run(argv,cwd=ROOT)
record.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
sys.exit(result.returncode)
