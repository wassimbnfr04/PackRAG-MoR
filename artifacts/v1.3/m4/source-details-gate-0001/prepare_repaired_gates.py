"""New drivers/bindings after a real product-layout correction; originals remain unchanged."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
records=[]
def derive(original,target,replacements):
    before=(HERE/original).read_text(encoding='utf-8');after=before
    for old,new in replacements:
        assert old in after,(original,old);after=after.replace(old,new)
    path=HERE/target;compile(after,str(path),'exec')
    if path.exists():assert path.read_text(encoding='utf-8')==after,'Existing partial derivation differs; never overwrite it'
    else:path.write_text(after,encoding='utf-8')
    records.append(dict(original=original,target=target,original_sha256=hashlib.sha256((HERE/original).read_bytes()).hexdigest(),new_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),replacements=replacements))
builds=[('build-0039','build-0041'),('build-0040','build-0042')]
derive('preflight.py','preflight_repaired.py',builds+[("prefix='pair' if args.pair else 'debug'","prefix='repaired-pair' if args.pair else 'repaired-debug'")])
derive('run_ui.py','run_ui_repaired.py',[builds[0]]+[("'pair-preflight.json'","'repaired-pair-preflight.json'"),
    ('device-ui-source-details-0001','device-ui-source-details-0002'),("'ui-execution.json'","'ui-execution-repaired.json'"),
    ("f'ui-stage-","f'ui-repaired-stage-")])
derive('run_full_phone.py','run_full_phone_repaired.py',builds+[("'ui-execution.json'","'ui-execution-repaired.json'"),
    ("'visual-inspection.json'","'visual-inspection-repaired.json'")])
derive('verify_retained.py','verify_retained_repaired.py',builds)
derive('verify_and_record.py','verify_and_record_repaired.py',builds+[("'ui-execution.json'","'ui-execution-repaired.json'"),
    ("'visual-inspection.json'","'visual-inspection-repaired.json'"),("'pair-preflight.json'","'repaired-pair-preflight.json'"),
    ("'verify_retained.py'","'verify_retained_repaired.py'"),('device-ui-source-details-0001','device-ui-source-details-0002')])
# Include the failed visual run and earlier source-bound builds as immutable evidence,
# without using their outcomes as final repaired-build acceptance.
path=HERE/'verify_and_record_repaired.py';text=path.read_text(encoding='utf-8')
needle="'build-0037','build-0038','build-0041','build-0042'"
assert text.count(needle)==1;text=text.replace(needle,"'build-0037','build-0038','build-0039','build-0040','build-0041','build-0042','device-ui-source-details-0001'")
path.write_text(text,encoding='utf-8');records[-1]['new_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
target=HERE/'repaired-gate-derivation.json';assert not target.exists()
target.write_text(json.dumps(dict(status='PREPARED_NEW_BINDINGS_NOT_REPAIRED_ACCEPTANCE',derivations=records,
    scope='Two changed Android UI layout sources require fresh host/APK/UI/full-development/full-policy/restoration. Python188/six desktop inputs unchanged; verify before bounded reuse.'),indent=2)+'\n',encoding='utf-8')
print('New repaired-build/UI/full/parity/closure drivers prepared; originals preserved')
