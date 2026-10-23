"""Durable phone gate state after actual four-method/visual PASS."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(HERE/'retained-ui-action-dispatch-execution.json')['status']=='PASS_E3_FOUR_RETAINED_UI_ORIGINALS_NOT_COMPLETE_E3'
assert read(HERE/'retained-ui-visual.json')['status']=='PASS_E3_RETAINED_AR_FR_CANONICAL_TESTED_VIEWPORT'
run=M4/'device-ui-diagnostics-retained-0004';collection=read(run/'collected-results.json');assert len(collection['saved_sha256'])==4
for n,v in collection['saved_sha256'].items():assert hashlib.sha256((run/'original-adb'/n).read_bytes()).hexdigest()==v
message='E3 current10 October20:26 UTC: retained UI0004 PASSES allfour methods216.928s, zero failed/ignored; allfour original JSONs, additional completed resubmission ownership original and two exact AR/FR PNGs saved before switch. Actual view_image confirms complete canonical text above navigation; retained-ui-visual PASS. Final0052/53 matched53 host/574 inputs, whole product APKs unchanged0048/49. Full background driver65092 RUNNING: new development37 then compiled-policy30, originals before each switch, restoreddebug0052/four-control consent0014, original collection, exact full parity/check-only/custody/closure/checkpoint. Do not kill/switch running tests or edit574 Android inputs. Owner may use phone normally with USB/mobile data on; keep PackRAG closed during default-registry byte guards. All earlier UI/host/Python/guard/visual failures remain immutable; no F code starts until E3 checkpoint. F read-only acceptance preparation is saved in M4F_ASSET_READINESS_PREPARATION.md. Final knowledge content owner supplied.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;text=p.read_text(encoding='utf-8-sig');first,rest=text.split('\n',1);p.write_text(first+'\n\n'+message+'\n'+rest,encoding='utf-8')
for name in ['docs/v1.3/M4E3_METHODS.md','docs/v1.3/M4E3_EVIDENCE_INDEX.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md']:
    with (ROOT/name).open('a',encoding='utf-8') as f:f.write('\n\n'+message+'\n\nThe new observation shows busy=true, old completion cleared, exact2028-02-29/MA-01 context and a distinct completion returning NO_RELEVANT_EVIDENCE. This proves new-run correctness, not the unobserved immediate timing of failed0002. Original0003 source-null failure remains preserved; repaired tests additionally wait actual action-state replacement before completion. No production behavior or expectation was changed.\n')
target=HERE/'full-background-start-state.json';assert not target.exists();target.write_text(json.dumps(dict(status='ACTUAL_RETAINED_UI_AND_VISUAL_PASS_FULL_BACKGROUND_RUNNING_NOT_E3_CLOSURE',recorded_utc=datetime.now(timezone.utc).isoformat(),driver_session=65092,
    ui_junit_methods=4,ui_junit_seconds=216.928,additional_ownership_report='m4-ui-query-resubmission-observation.json',ordinary_phone_use_allowed=True,keep_packrag_closed=True,
    planned_background_methods=dict(development=37,compiled_policy=30,restore=1)),indent=2)+'\n',encoding='utf-8')
print('Actual UI/visual PASS and full background65092 durable state saved')
