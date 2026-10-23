"""Record actual view_image review of the two completed repaired UI captures."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
ui=json.loads((HERE/'ui-execution-repaired.json').read_text(encoding='utf-8'))
assert ui['status']=='PASS_FOUR_UI_METHODS_ORIGINALS_AND_SCREENSHOTS_SAVED_NOT_VISUAL_OR_E2_CLOSURE'
for name,value in ui['original_png_sha256'].items():assert hashlib.sha256((M4/'device-ui-source-details-0002/original-adb'/name).read_bytes()).hexdigest()==value
target=HERE/'visual-inspection-repaired.json';assert not target.exists()
target.write_text(json.dumps(dict(status='PASS_AR_FR_CANONICAL_DISPLAY_NOT_SEMANTIC_REVIEW',inspected_utc=datetime.now(timezone.utc).isoformat(),
    image_sha256=ui['original_png_sha256'],method='Both actual local PNGs displayed by view_image and visually inspected in this turn.',
    observations=['Arabic canonical text appears on two readable right-directed lines above all three system navigation buttons, without the previous fading/occlusion.',
        'French canonical text appears on two readable left-directed lines, preserving accented characters and 74 °C; the final line is clear above navigation.',
        'Both screenshots are intentionally scrolled to canonical content; upper metadata at the viewport boundary is not a claim that the full long source screen fits simultaneously.',
        'Existing test asserts the exact canonical strings and separately the actual English generator rendering; viewing a screenshot does not substitute for byte/hash parity.'],
    limits=['Signed synthetic viewer-component records, not new multilingual inference or production admission of custom fixture keys.',
        'No external document, genuine translation review, licensing approval or semantic entailment assessment.',
        'Visual check is limited to this phone/configuration and these two captures; broader accessibility/lifecycle hardening remains E3.'],
    original_visual_failure_preserved=True),indent=2)+'\n',encoding='utf-8')
print('Actual repaired Arabic/French screenshots inspected and bound; original visual FAIL preserved')
