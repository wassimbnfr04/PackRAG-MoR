"""Execute only after actual view_image inspection of both new original canonical PNGs."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;run=ROOT/'artifacts/v1.3/m4/device-ui-diagnostics-retained-0003'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(HERE/'retained-ui-resubmission-execution.json')['status']=='PASS_E3_FOUR_RETAINED_UI_ORIGINALS_NOT_COMPLETE_E3'
target=HERE/'retained-ui-visual.json';assert not target.exists();images={}
for row in read(run/'m4-source-details-languages-ui.json')['cases']:
    p=run/'original-adb'/row['screenshot'];v=hashlib.sha256(p.read_bytes()).hexdigest();assert v==row['screenshot_sha256']
    images[p.name]=v
assert set(images)=={'m4-source-details-ar.png','m4-source-details-fr.png'}
record=dict(status='PASS_E3_RETAINED_AR_FR_CANONICAL_TESTED_VIEWPORT',recorded_utc=datetime.now(timezone.utc).isoformat(),
    original_png_sha256=images,review_method='Both exact newly saved original PNGs actually inspected with view_image.',
    scope='Complete canonical AR/FR text readable above safe navigation region in tested phone viewport. This is a fresh retained presentation regression, not genuine translation/reviewer approval or all-device accessibility acceptance.',
    provenance='Previously rejected E2 visual captures and earlier repaired acceptance remain immutable. No cropped/edited/generated replacement image used.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
