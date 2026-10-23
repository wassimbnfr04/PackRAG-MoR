"""Pre-execution collector-contract correction; no Android source change."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
p=HERE/'run_retained_ui_resubmission.py';target=HERE/'resubmission-collection-driver-repair.json';assert not target.exists()
saved=HERE/'run_retained_ui_resubmission.before-collector-contract.py';assert not saved.exists();saved.write_bytes(p.read_bytes())
source=p.read_text(encoding='utf-8');before=',m4-ui-query-resubmission-observation.json\']';assert source.count(before)==1
source=source.replace(before,"']")
before='images={}\n'
after='''# The optional observation has a deliberately detailed stage status rather than the generic PASS contract.
name='m4-ui-query-resubmission-observation.json'
command=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell','run-as','org.packrag.product','cat','files/'+name]
result=subprocess.run(command,capture_output=True,check=True,timeout=30);observation=json.loads(result.stdout)
assert observation['status']=='PASS_NEW_COMPLETION_EDITED_CONTEXT_ABSTENTION'
assert observation['new_completion_id']!=observation['previous_completion_id'] and observation['new_answer_state']=='NO_RELEVANT_EVIDENCE'
saved=run/'original-adb'/name;assert not saved.exists();saved.write_bytes(result.stdout)
primary=run/name;assert not primary.exists();primary.write_bytes(result.stdout)
record=run/'collected-resubmission-observation.json';assert not record.exists()
record.write_text(json.dumps(dict(status='PASS',argv=command,returncode=result.returncode,original_sha256=hashlib.sha256(result.stdout).hexdigest(),scope='Additional completed-query ownership observation, separate from four generic PASS method reports.'),indent=2)+'\\n',encoding='utf-8')
images={}
'''
assert source.count(before)==1;source=source.replace(before,after);compile(source,str(p),'exec');p.write_text(source,encoding='utf-8')
target.write_text(json.dumps(dict(status='PRE_EXECUTION_OBSERVATION_COLLECTION_CONTRACT_CORRECTED',before_sha256=hashlib.sha256(saved.read_bytes()).hexdigest(),after_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
    reason='Generic collector requires exactly status PASS. Optional new ownership report deliberately has descriptive stage status. Keep four unchanged PASS reports in generic collector; separately capture/check observation only after successful suite. No device command had run; no tests relaxed.'),indent=2)+'\n',encoding='utf-8')
print('Driver contract corrected before execution, original bytes retained')
