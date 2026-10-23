"""Resolve identified old restoration output collision without touching active tests/history."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
target=HERE/'restoration-path-collision-preparation.json';assert not target.exists()
old=M4/'device-development-restore-0014';assert old.is_dir() and not (M4/'device-development-restore-0015').exists()
prior=read(M4/'source-details-gate-0001/gate.json');guard={n:v for n,v in prior['output_sha256'].items() if n.startswith(old.relative_to(ROOT).as_posix()+'/')};assert guard
for n,v in guard.items():assert sha(ROOT/n)==v,n
original_manifest=read(old/'instrumentation-manifest.json');assert original_manifest['started_at']=='2026-10-10T16:49:32.311466+00:00'
runner=ROOT/'scripts/v13_test_android.py';source=runner.read_text(encoding='utf-8');assert source.index('args.run.mkdir(parents=True, exist_ok=False)')<source.index('record = dict(')<source.index('for path in apks:')
rows=[]
def derive(before_name,after_name,changes):
    original=HERE/before_name;content=original.read_text(encoding='utf-8')
    for before,after in changes:assert before in content,before;content=content.replace(before,after)
    p=HERE/after_name;compile(content,str(p),'exec')
    if p.exists():assert p.read_text(encoding='utf-8')==content,'Existing preparation prefix differs'
    else:p.write_text(content,encoding='utf-8')
    rows.append(dict(original=before_name,original_sha256=sha(original),derived=after_name,derived_sha256=sha(p),replacements=changes))
derive('verify_full_parity_dispatch_final.py','verify_full_parity_restoration_final.py',[
    ('full-background-execution.json','full-background-recovered-execution.json'),('device-development-restore-0014','device-development-restore-0015')])
derive('verify_and_record.py','verify_and_record_final.py',[
    ('full-background-execution.json','full-background-recovered-execution.json'),('device-development-restore-0014','device-development-restore-0015'),
    ('verify_full_parity_dispatch_final.py','verify_full_parity_restoration_final.py')])
derive('update_acceptance_documents.py','update_acceptance_documents_final.py',[
    ('verify_and_record.py','verify_and_record_final.py'),('device-development-restore-0014','device-development-restore-0015')])
target.write_text(json.dumps(dict(status='OLD_RESTORATION_PATH_COLLISION_IDENTIFIED_FRESH0015_RECOVERY_PREPARED_NOT_EXECUTED',recorded_utc=datetime.now(timezone.utc).isoformat(),
    active_driver_session=65092,old_restoration_manifest_sha256=sha(old/'instrumentation-manifest.json'),old_e2_public_outputs_guard=guard,runner_sha256=sha(runner),
    derivations=rows,scope='Current driver already loaded0014 restoration argv. Let both current full suites and original collectors finish; its eventual mkdir FileExists failure occurs before phone mutation. Preserve that failed orchestration record. Fresh0015 same0052 consent method/original must pass; only then recovered execution/parity/closure, with no old result promoted or overwritten.'),indent=2)+'\n',encoding='utf-8')
message='E3 current10 October20:39 UTC: current full37 development RUNNING65092, four methods passed in observed log, zero reported failure. Prepared restoration path0014 is discovered to already hold immutable E2 build0039 evidence from16:49 UTC. Existing runner mkdir(exist_ok=False) executes before record/ADB, so it will refuse old path without touching historical files or phone. Current loaded driver cannot acquire a new argv by editing its source; do not kill tests. Let full37/30 and collectors finish, preserve eventual stage4 orchestration FileExists failure, then prepared fresh0015 debug0052 consent/original recovery. New parity/closure/document helpers explicitly reference recovered execution and0015. No failed product test or new acceptance inferred;574 Android inputs stay frozen, F/later held.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;text=p.read_text(encoding='utf-8-sig');first,rest=text.split('\n',1);p.write_text(first+'\n\n'+message+'\n'+rest,encoding='utf-8')
for name in ['docs/v1.3/M4E3_METHODS.md','docs/v1.3/M4E3_EVIDENCE_INDEX.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md']:
    with (ROOT/name).open('a',encoding='utf-8') as f:f.write('\n\n'+message+'\n\nThe path was inherited from prepared drivers and should have been checked for absence before start. Correction preserves original driver/verifier bytes and all old0014 outputs; source-supported before-ADB refusal is not yet an executed failure. Restoration-path-collision-preparation.json binds the old immutable records and precise new helper derivations.\n')
print('Old immutable0014 preserved; fresh0015 recovery/parity/closure prepared, current tests unchanged')
