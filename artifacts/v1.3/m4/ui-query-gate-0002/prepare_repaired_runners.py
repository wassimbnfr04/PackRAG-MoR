"""Mechanical fresh-output adapters for the one test-only UI repair."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent
rules={
    'preflight.py':('preflight_repaired.py',{'build-0033':'build-0035','build-0034':'build-0036',"'preflight.json'":"'preflight-repaired.json'","mode+'.txt'":"'repaired-'+mode+'.txt'","'permissions.txt'":"'repaired-permissions.txt'","'badging.txt'":"'repaired-badging.txt'","'policy-apk-entries.txt'":"'repaired-policy-apk-entries.txt'","'packaged-release-trust.json'":"'repaired-packaged-release-trust.json'"}),
    'run_ui.py':('run_ui_repaired.py',{'build-0033':'build-0035','device-ui-query-0001':'device-ui-query-0002',"'ui-execution.json'":"'ui-execution-0002.json'",'ui-stage-{i}':'ui0002-stage-{i}'}),
    'run_device_gates.py':('run_device_gates_repaired.py',{'build-0033':'build-0035','build-0034':'build-0036',"'ui-execution.json'":"'ui-execution-0002.json'","'preflight.json'":"'preflight-repaired.json'"})
}
records=[]
for name,(target,replacements) in rules.items():
    original=(HERE/name).read_bytes();updated=original.decode('utf-8');counts={}
    for old,new in replacements.items():
        counts[old]=updated.count(old);assert counts[old]>0,(name,old);updated=updated.replace(old,new)
    destination=HERE/target;assert not destination.exists();destination.write_text(updated,encoding='utf-8')
    compile(updated,str(destination),'exec')
    records.append(dict(original=name,new=target,original_sha256=hashlib.sha256(original).hexdigest(),new_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),replacements=replacements,counts=counts))
record=HERE/'repaired-runner-derivations.json';assert not record.exists();record.write_text(json.dumps(records,indent=2)+'\n')
print('Three exact fresh-output runner adapters saved')
