"""Durable active-phase handoff; never claim running work passed."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
target=HERE/'ui-retry-running-0001.json';assert not target.exists()
proof=HERE/'ui-assertion-repair-build-proof-0001.json';assert json.loads(proof.read_text())['status']=='PASS_SINGLE_TEST_REPAIR_PRODUCT_APK_IDENTICAL_NOT_UI_ACCEPTANCE'
note=('M4F2 actual system-picker retry UI0002 RUNNING '+datetime.now(timezone.utc).isoformat()+': debug0071 passes73 host methods/598 frozen inputs/contracts and has byte-identical product APK to0069/0067,597 other inputs unchanged. Exactly one test source explicitly requests substring comparison for three UI fragments, preserving semantic expectations. Actual initial UI0001 FAIL149.932s preserved, two recorded passing cases only; failure-time main/PNG captures are cat error bytes, not valid result/images. Known50 unchanged after failure. Approved-only full-slot/native0070 actual eight controls234.251s and original/source/owner guards already pass. Owner explicitly authorized current announced ten-minute unlocked untouched window; retry launched using run_picker_ui_retry.py. No compile/install/source edits or killing this active test; wait terminal and save original JSON/PNGs before any switch, then independent visible-scope image review. Full F2 still needs adjacent guard repair/regressions/final policy pairing/restoration/custody/closure/checkpoint; F3 prepared only/F4 pending. Mobile data stays on, final packs owner supplied; no full M4/product acceptance.')
record=dict(status='RUNNING_F2_UI_RETRY_NOT_ACCEPTED',recorded_utc=datetime.now(timezone.utc).isoformat(),note=note)
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as s:s.write('\n\n'+note+'\n')
print(record['status'])
