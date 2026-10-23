"""Fresh final drivers; retain original failed/pending driver bytes."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
target=HERE/'resubmission-driver-preparation.json';assert not target.exists();rows=[]
def derive(old,new,changes):
    original=HERE/old;source=original.read_text(encoding='utf-8')
    for before,after in changes:
        assert before in source,before;source=source.replace(before,after)
    dest=HERE/new;assert not dest.exists();dest.write_text(source,encoding='utf-8')
    rows.append(dict(original=old,original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),derived=new,derived_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),replacements=changes))
derive('run_retained_ui_retry.py','run_retained_ui_resubmission.py',[
    ('build-0048','build-0050'),('device-ui-diagnostics-retained-0002','device-ui-diagnostics-retained-0003'),
    ('retained-ui-retry-execution.json','retained-ui-resubmission-execution.json'),('retained-ui-retry-stage-','retained-ui-resubmission-stage-'),
    ('foreground-retained-retry-readiness.json','foreground-retained-resubmission-readiness.json'),
    ("policy-diagnostics-preflight.json')['status']=='PASS_E3_MATCHED_POLICY_PAIR_NOT_ACTUAL_POLICY_OR_FULL_E3'","resubmission-preflight.json')['status']=='PASS_E3_TEST_ONLY_RESUBMISSION_MATCHED_PAIR_NOT_DEVICE_ACCEPTANCE'"),
    ('m3-pack-management-ui.json\']','m3-pack-management-ui.json,m4-ui-query-resubmission-observation.json\']')])
derive('record_foreground_retained_retry.py','record_foreground_retained_resubmission.py',[
    ('foreground-retained-retry-readiness.json','foreground-retained-resubmission-readiness.json'),
    ('received after foreground interruption; no new reply is invented.','retained as current authorization for corrected final query synchronization and announced new window; no new reply is invented.')])
derive('record_retained_visual_retry.py','record_retained_visual_resubmission.py',[
    ('device-ui-diagnostics-retained-0002','device-ui-diagnostics-retained-0003'),('retained-ui-retry-execution.json','retained-ui-resubmission-execution.json')])
derive('run_full_background.py','run_full_background_final.py',[
    ('retained-ui-retry-execution.json','retained-ui-resubmission-execution.json'),('build-0048','build-0050'),('build-0049','build-0051')])
derive('verify_full_parity.py','verify_full_parity_final.py',[('build-0048','build-0050'),('build-0049','build-0051')])
target.write_text(json.dumps(dict(status='PREPARED_FRESH_STRONGER_QUERY_UI_AND_MATCHED_BACKGROUND_DRIVERS_NOT_EXECUTION',derivations=rows),indent=2)+'\n',encoding='utf-8')
print('Fresh final UI/background/parity/readiness/visual drivers prepared')
