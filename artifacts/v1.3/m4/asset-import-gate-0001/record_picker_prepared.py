"""Persist exact prepared foreground gate, without claiming it ran."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
target=HERE/'picker-prepared-0001.json';assert not target.exists()
prep=ROOT/'artifacts/v1.3/m4/device-local-asset-picker-preparation-0001'
raw=prep/'original-adb/m4-local-asset-picker-preparation.json'
assert read(raw)['status']=='PASS' and sha(raw)==read(prep/'collected-results.json')['saved_sha256'][raw.name]
assert read(HERE/'picker-preparation-0001-after-known-guard.json')['status']=='PASS_KNOWN50_EXISTING_PUBLIC_FILES_UNCHANGED'
sources=read(ROOT/'artifacts/v1.3/m4/build-0069/source-at-build-start.json')['files']
for name,value in sources.items():assert sha(ROOT/name)==value,name
note=('M4F2 system-picker gate PREPARED '+datetime.now(timezone.utc).isoformat()+': build0069/frozen598/host73 and actual background picker-preparation0001 pass, original saved/hash-bound, known50 unchanged. Target package lookup null; explicit shell OPEN_DOCUMENT octet-stream resolves DocumentsUI; product MANAGE_DOCUMENTS denied and unselected protected document read denied. This is preparation only, no selection/UI acceptance. Product APK byte-identical to physically passing ViewModel0067. Concrete run_picker_ui.py and M4F2_SYSTEM_PICKER_METHODS.md bind eight actual picker/cancel/corrupt/progress/recreation/result/navigation/new native answer/owner controls, two exact PNGs requiring independent visible-scope review, original capture before switch and failure preservation. Fresh ten-minute unlocked untouched-phone window requested; do not infer approval from elapsed time. Background work remains authorized. Approved-policy and retained regression/restoration/custody/closure/checkpoint remain before F3/F4. Owner final packs excluded; mobile data stays on. User explicitly directed completion of all M4; status questions do not cancel continuous work.')
record=dict(status='PREPARED_F2_UI_NOT_EXECUTED_OR_ACCEPTED',recorded_utc=datetime.now(timezone.utc).isoformat(),runner_sha256=sha(HERE/'run_picker_ui.py'),methods_sha256=sha(ROOT/'docs/v1.3/M4F2_SYSTEM_PICKER_METHODS.md'),preparation_original_sha256=sha(raw),note=note)
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as s:s.write('\n\n'+note+'\n')
print(record['status'])
