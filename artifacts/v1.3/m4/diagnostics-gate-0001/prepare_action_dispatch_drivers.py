"""Fresh UI0004/final pair drivers; preserve earlier failed and unexecuted drivers."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
target=HERE/'action-dispatch-driver-preparation.json';assert not target.exists();rows=[]
def derive(old,new,changes):
    original=HERE/old;source=original.read_text(encoding='utf-8')
    for before,after in changes:
        assert before in source,before;source=source.replace(before,after)
    dest=HERE/new;assert not dest.exists();compile(source,str(dest),'exec');dest.write_text(source,encoding='utf-8')
    rows.append(dict(original=old,original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),derived=new,derived_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),replacements=changes))
derive('run_retained_ui_resubmission.py','run_retained_ui_action_dispatch.py',[
    ('build-0050','build-0052'),('device-ui-diagnostics-retained-0003','device-ui-diagnostics-retained-0004'),
    ('retained-ui-resubmission-execution.json','retained-ui-action-dispatch-execution.json'),('retained-ui-resubmission-stage-','retained-ui-action-dispatch-stage-'),
    ('foreground-retained-resubmission-readiness.json','foreground-retained-action-dispatch-readiness.json'),
    ('resubmission-preflight.json','action-dispatch-preflight.json'),('PASS_E3_TEST_ONLY_RESUBMISSION_MATCHED_PAIR_NOT_DEVICE_ACCEPTANCE','PASS_E3_TEST_ONLY_ACTION_DISPATCH_MATCHED_PAIR_NOT_DEVICE_ACCEPTANCE')])
derive('record_foreground_retained_resubmission.py','record_foreground_retained_action_dispatch.py',[
    ('foreground-retained-resubmission-readiness.json','foreground-retained-action-dispatch-readiness.json'),
    ('corrected final query synchronization','corrected two action-dispatch waits')])
derive('record_retained_visual_resubmission.py','record_retained_visual_action_dispatch.py',[
    ('device-ui-diagnostics-retained-0003','device-ui-diagnostics-retained-0004'),('retained-ui-resubmission-execution.json','retained-ui-action-dispatch-execution.json')])
derive('run_full_background_final.py','run_full_background_dispatch_final.py',[
    ('retained-ui-resubmission-execution.json','retained-ui-action-dispatch-execution.json'),('build-0050','build-0052'),('build-0051','build-0053')])
derive('verify_full_parity_final.py','verify_full_parity_dispatch_final.py',[('build-0050','build-0052'),('build-0051','build-0053')])
target.write_text(json.dumps(dict(status='PREPARED_FRESH_STRONG_ACTION_DISPATCH_UI_AND_FINAL_BACKGROUND_DRIVERS_NOT_EXECUTION',derivations=rows),indent=2)+'\n',encoding='utf-8')
print('Fresh final UI0004/background/parity/readiness/visual drivers prepared')
