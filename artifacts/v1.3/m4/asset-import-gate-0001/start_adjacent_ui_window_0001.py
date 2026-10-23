"""Record the already-authorized foreground window only after the background gate passes."""
import hashlib,json
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
target=HERE/'adjacent-ui-window-start-0001.json';assert not target.exists()
authorization=HERE/'adjacent-ui-window-authorization-0001.json'
assert read(authorization)['status']=='AUTHORIZED_FUTURE_ANNOUNCED_WINDOW_NOT_RUNNING_OR_ACCEPTED'
background=HERE/'device-local-asset-adjacent-debug-0001-execution.json'
assert read(background)['status']=='PASS_F2_FRESH_ADJACENT_BACKGROUND_VARIANT_NOT_FULL_F2'
assert read(background)['build']=='build-0076'
now=datetime.now(timezone.utc)
record=dict(status='AUTHORIZED_ANNOUNCED_UI_WINDOW_STARTED_NOT_TEST_ACCEPTANCE',started_utc=now.isoformat(),
 launch_deadline_utc=(now+timedelta(minutes=20)).isoformat(),authorization_sha256=sha(authorization),background_sha256=sha(background),
 build='build-0076',selections=['management','query','sources','diagnostics','assets'],
 scope='Owner agreed20-minute unlocked/untouched window; announce actual start. No new UI class starts after this deadline without renewed explicit authorization; an already-running class may finish. Mobile data stays on. All five actual original reports/PNGs and visible-scope reviews required separately. No installation/source edits during window.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['started_utc'],record['launch_deadline_utc'])
