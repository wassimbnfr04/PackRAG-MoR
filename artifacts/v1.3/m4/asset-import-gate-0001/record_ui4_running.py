"""Record final submission-retry activity and correct the earlier stopped-only assumption."""
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
target=HERE/'ui4-running-0001.json';assert not target.exists()
note=('UI0004 RUNNING '+datetime.now(timezone.utc).isoformat()+' on debug0073/frozen598/host73, whole product APK unchanged0067/69/71/72/73. Owner authorized a new announced7-minute unlocked untouched window. No compile/install/tested-source edits until terminal and original collection. UI0001/2/3 remain FAIL149.932/189.619/156.632s with actual partial evidence; UI3 passes six controls and actual recreation/official grant/install/source navigation but fails unchanged final completion ID. Test now checks actual form/enabled button/idle then tap, requires observed new query start before waiting for final new-ID/cold native/canonical/cited answer. No tap retry or substituted generation. Important lifecycle correction: UI3 physically observed STARTED (paused), not CREATED (fully stopped), at recreation request behind DocumentsUI; actual destruction/distinct new instance/saved bundle/same ViewModel/picker foreground all pass. Initial preparation helper incorrectly required CREATED, its failed script and assumption record are preserved; new validator accepts non-resumed STARTED or CREATED and keeps every actual recreation fact mandatory. Earlier prose referring to UI3 as stopped must be read with this explicit correction; no whole-phone restart proof. Known50 after each failure unchanged; approved-policy full4 import/cold/warm0070 passed8 controls234.251s with originals saved. Full F2 requires final UI/visual/adjacent guard repairs/matched regressions/restoration/custody/closure/checkpoint before F3/F4; no full M4/product acceptance. User directed continuous completion of all M4; final knowledge content excluded/mobile data on.')
target.write_text(json.dumps(dict(status='RUNNING_F2_UI4_NOT_ACCEPTED',recorded_utc=datetime.now(timezone.utc).isoformat(),note=note),indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as s:s.write('\n\n'+note+'\n')
print('RUNNING_F2_UI4_NOT_ACCEPTED')
