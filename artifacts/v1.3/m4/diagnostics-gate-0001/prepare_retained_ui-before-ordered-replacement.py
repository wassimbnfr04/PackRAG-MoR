"""Adapt immutable E2 driver only for current builds/results and E3 prerequisites."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
original=M4/'source-details-gate-0001/run_ui_repaired.py';source=original.read_text(encoding='utf-8')
gate=json.loads((M4/'source-details-gate-0001/gate.json').read_text(encoding='utf-8'))
assert sha(original)==gate['output_sha256'][original.relative_to(ROOT).as_posix()]
changes=[("assert read(HERE/'repaired-pair-preflight.json')['matched_variants']", "assert read(HERE/'policy-diagnostics-preflight.json')['status']=='PASS_E3_MATCHED_POLICY_PAIR_NOT_ACTUAL_POLICY_OR_FULL_E3'"),
    ("assert read(HERE/'focused-device-execution.json')['status']=='PASS_NEW_E2_BACKGROUND_METHODS_ORIGINALS_SAVED_NOT_E2_CLOSURE'", "assert read(HERE/'policy-diagnostics-execution.json')['status']=='PASS_E3_ACTUAL_COMPILED_POLICY_DIAGNOSTICS_ORIGINAL_NOT_COMPLETE_E3'\nassert read(HERE/'foreground-retained-readiness.json')['owner_quote']=='GO AHEAD ILL LEAVE THE PHONE UNTOUCHED'"),
    ('device-ui-source-details-0002','device-ui-diagnostics-retained-0001'),('build-0041','build-0048'),
    ('ui-execution-repaired.json','retained-ui-execution.json'),('ui-repaired-stage-','retained-ui-stage-'),
    ('PASS_FOUR_UI_METHODS_ORIGINALS_AND_SCREENSHOTS_SAVED_NOT_VISUAL_OR_E2_CLOSURE','PASS_E3_FOUR_RETAINED_UI_ORIGINALS_NOT_COMPLETE_E3'),
    ('E2 UI','E3 retained UI'),('E2_UI_ORIGINALS_AND_PNGS_SAVED_VISUAL_QA_PENDING','E3_RETAINED_UI_ORIGINALS_AND_PNGS_SAVED_VISUAL_QA_PENDING'),
    ('E2 UI gate failed','E3 retained UI gate failed')]
for before,after in changes:
    assert before in source,before;source=source.replace(before,after)
target=HERE/'run_retained_ui.py';assert not target.exists();target.write_text(source,encoding='utf-8')
ready=HERE/'record_foreground_retry.py';value=ready.read_text(encoding='utf-8');assert value.count('foreground-retry-readiness.json')==1
value=value.replace('foreground-retry-readiness.json','foreground-retained-readiness.json')
target=HERE/'record_foreground_retained.py';assert not target.exists();target.write_text(value,encoding='utf-8')
record=dict(status='PREPARED_CURRENT_RETAINED_UI_NOT_EXECUTION',original_driver_sha256=sha(original),replacements=changes,
    derived_driver_sha256=sha(HERE/'run_retained_ui.py'),original_readiness_sha256=sha(ready),derived_readiness_sha256=sha(target),
    scope='Same four retained foreground methods and expectations, fresh0048 output paths; real readiness/owner window/original collection/new visual inspection still required.')
target=HERE/'retained-ui-preparation.json';assert not target.exists();target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
