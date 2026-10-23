"""Close failed installer attempts factually and persist the exact next action."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
target=HERE/'visual-retry-pending-0001.json';assert not target.exists()
names=['device-local-asset-import-visual-0001-execution.json',
       'device-local-asset-import-visual-0002-execution.json',
       'visual-installed-state-0001.json','visual-installed-retry-preparation-0001.json',
       'visual0002-application-exit-info.txt','package-install-screen-0001.png',
       'package-install-screen-0002.png','visual-failed-0002-after-known-guard.json',
       'visual-failed-0002-after-source.json','adjacent-guard-preparation-0001.json']
identities={}
for name in names:
    with (HERE/name).open('rb') as stream:identities[name]=hashlib.file_digest(stream,'sha256').hexdigest()
assert json.loads((HERE/names[0]).read_text())['status']=='FAIL'
assert json.loads((HERE/names[1]).read_text())['status']=='FAIL'
progress=json.loads((ROOT/'artifacts/v1.3/m4/device-local-asset-import-visual-0002/failure-original-adb/m4-local-asset-import-visual-progress.json').read_text())
assert progress['current_point']=='PREPARING' and progress['cases']==[]
note=(
    'M4F2 separate visual gate PENDING after two preserved failed attempts; no test/build running. '
    'Visual0001 failed product streamed installation timeout180s before instrumentation. '
    'Visual0002 non-streaming product/test installs both succeeded; actual selected instrumentation '
    'started and progress test_id '+progress['test_id']+' reached PREPARING with zero passed cases '
    'before process termination. Android exit-info records PID9269 at19:33:05.792 reason16 '
    'PACKAGE UPDATED, stop due to installPackageLI; not a demonstrated Java/native runtime crash. '
    'Earlier record_install_prompt prose saying visual0002 awaited installer/no instrumentation '
    'was a timing inference and is superseded by these collected actual terminal facts, retained '
    'unchanged for audit. Screenshot0001 shows actual Play Protect send-to-Google dialog; '
    'screenshot0002 shows launcher and no dialog. Actor/choice/installer-session attribution is '
    'unknown; no agent upload or security-setting bypass. I retried before a timed-out installer '
    'was proven settled; fixed by exact installed75 product/test APK SHA256 checks and new runner '
    'with no reinstall. Both hashes now exact; frozen599 inputs/product APK/UI0004 retained598 '
    'remain unchanged. Known50 owner public files and readonly full source4 unchanged after '
    'these failures. Any interrupted isolated f2-visual root is retained for bounded closure '
    'inspection, not silently removed or counted as success. Eleven guard-only proposals '
    'validated but not applied; active Android sources unchanged. Previous untouched window '
    'ended; fresh4-minute owner confirmation requested and required before next foreground test. '
    'Next command: .venv-pack/Scripts/python.exe -X utf8 '
    'artifacts/v1.3/m4/asset-import-gate-0001/run_visual_installed_0001.py '
    '--build build-0075 --run device-local-asset-import-visual-0003 --foreground-authorized. '
    'Then save originals and independently inspect both unmodified settled PNGs; accept only '
    'actual readable full viewport. UI0004 eight controls/native PHONEPASS remains separate '
    'from its original VISUALFAIL. Full F2 safe adjacent regressions/matched policy/restoration '
    'custody/immutable closure/checkpoint pending; F3 presentation/a11y and F4 comprehensive '
    'audit remain held. Full M4/system/product not complete; continuous M4 mandate preserved. '
    'Owner final knowledge packs excluded; mobile data on.'
)
target.write_text(json.dumps(dict(status='READY_VERIFIED_INSTALLED_VISUAL_RETRY_PENDING_FRESH_FOREGROUND_WINDOW',recorded_utc=datetime.now(timezone.utc).isoformat(),evidence_sha256=identities,note=note),indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    path=ROOT/name;header,rest=path.read_text(encoding='utf-8').split('\n',1)
    path.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md','docs/v1.3/M4F2_SYSTEM_PICKER_METHODS.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print('READY_VERIFIED_INSTALLED_VISUAL_RETRY_PENDING_FRESH_FOREGROUND_WINDOW')
