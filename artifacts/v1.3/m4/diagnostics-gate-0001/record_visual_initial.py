"""Actual view_image review: preserve automated PASS but reject incomplete home capture."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;run=ROOT/'artifacts/v1.3/m4/device-ui-diagnostic-navigation-0001'
target=HERE/'navigation-visual-initial.json';assert not target.exists()
data=json.loads((run/'m4-diagnostic-navigation.json').read_text());rows={}
for name,row in data['visual_png'].items():
    p=run/'original-adb'/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'] and p.stat().st_size==row['bytes']
    rows[name]=row
record=dict(status='FAIL_HOME_DIAGNOSTIC_MEASUREMENTS_NOT_VISIBLE_SOURCE_CANONICAL_VISIBLE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    images=rows,review_method='Both exact original PNGs inspected with view_image, not inferred from test tags.',
    home='Accepted answer/citation/header are readable, but IME occupies the lower half; only diagnostics heading reaches the viewport. Numeric diagnostic observations are not visually demonstrated.',
    source='Canonical English sentence including74°C is complete above navigation; attribution/unknown fields are readable. Tested viewport only.',
    automated_scope='JUnit one method/seven controls106.073s and original JSON PASS stay unchanged; visual acceptance fails independently.',
    next='Hold later policy/full acceptance. Preserve0046/test/source/screenshots; repair capture-only hide-IME/measurement anchor, fresh build and actual UI retry. Do not alter old PNGs.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
