"""Record the separately authorized, frozen visual experiment without accepting it."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
target = HERE / 'visual-running-0001.json'
assert not target.exists()
note = (
    'Separate picker visual0001 RUNNING ' + datetime.now(timezone.utc).isoformat() +
    ' under build0075: 73 host methods/599 inputs and packaging contracts pass; '
    'all598 UI0004 inputs and whole product APK unchanged, only the separate visual test added. '
    'Owner explicitly replied Yes, retry now; phone unlocked/untouched window announced. '
    'Actual picker slow-template progress/cancel and official-template verified import use isolated '
    'template-only root; no native generation or all-four-ready claim. Unmodified PNGs are sampled '
    'after750ms and three equal static-grid frames250ms apart; changing counter/indicator and '
    'status/navigation margins are excluded from the settling fingerprint only, never from saved PNGs. '
    'Independent visual review is mandatory after original collection. UI0004 eight phone controls '
    'and native result remain separately dated PASS; its two original images remain visual FAIL. '
    'Build0074 compiled but was never executed; pre-Activity Compose-idle dependency was corrected '
    'before execution in0075, not an observed product/phone failure. No source/build/APK switch '
    'during this test. F2 adjacent safe-guard regressions/matched policy/restoration/custody/closure '
    'and checkpoint remain; F3/F4 held. Mobile data remains on; owner final knowledge packs excluded.'
)
target.write_text(json.dumps(dict(status='RUNNING_SEPARATE_VISUAL_NOT_ACCEPTED', note=note), indent=2)+'\n', encoding='utf-8')
for name in ['STATUS.md', 'PLAN.md']:
    path = ROOT / name
    header, rest = path.read_text(encoding='utf-8').split('\n', 1)
    path.write_text(header+'\n\n'+note+'\n\n'+rest, encoding='utf-8')
for name in ['DECISIONS.md', 'docs/v1.3/FULL_DOCUMENTATION_WORKING.md', 'docs/v1.3/M4_IMPLEMENTATION_LOG.md', 'docs/v1.3/M4F2_SYSTEM_PICKER_METHODS.md']:
    with (ROOT/name).open('a', encoding='utf-8') as stream:
        stream.write('\n\n'+note+'\n')
print('RUNNING_SEPARATE_VISUAL_NOT_ACCEPTED')
