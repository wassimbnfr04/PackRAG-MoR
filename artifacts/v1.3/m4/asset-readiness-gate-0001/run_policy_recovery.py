"""Continue only after strict legacy schema recovery; keep the first failed sequence intact."""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'policy-and-restoration-recovery-0001.json';assert not target.exists()
prior=read(HERE/'policy-and-restoration-execution-0001.json');assert prior['status']=='FAIL' and len(prior['commands'])==4
sidecar=read(HERE/'policy-schema-and-owner-guard-0001.json');assert sidecar['status']=='PASS_ACTUAL_POLICY_PHASE_FINAL_OWNER_GUARD_AND_UNCHANGED_LEGACY_SCHEMA_NOT_CLOSURE'
assert sidecar['failed_driver_sha256']==sha(HERE/'policy-and-restoration-execution-0001.json')
verified=read(HERE/'device-local-assets-policy-adjacent-0001-verified.json')
assert verified['status']=='PASS_F1_ADJACENT_INDEPENDENT_ORIGINAL_CONTRACT_CHECK_NOT_CLOSURE'
assert verified['legacy_policy_guard_sidecar_sha256']==sha(HERE/'policy-schema-and-owner-guard-0001.json')
assert read(HERE/'adjacent-retained-parity-demo-0001.json')['cases']==13
inputs=read(M4/'build-0056/source-at-build-start.json')['files'];assert len(inputs)==579
assert inputs==read(M4/'build-0057/source-at-build-start.json')['files']
for name,value in inputs.items():assert sha(ROOT/name)==value,name
restored=M4/'device-local-assets-development-restore-0001';assert not restored.exists()
assert not (HERE/'current-source-at-closure.json').exists() and not (HERE/'owner-at-closure.json').exists()
python=[sys.executable,'-X','utf8'];commands=[
    python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0056'),'--run',str(restored),
        '--class-name','org.packrag.product.PackImportConsentTest','--result-file','m3-import-consent.json','--timeout','900','--variant','debug'],
    python+['-m','scripts.v13_collect_phone_results','--run',str(restored),'--files','m3-import-consent.json'],
    python+['-m','scripts.v13_android_source_identity','--output',str(HERE/'current-source-at-closure.json')],
    python+[str(HERE/'capture_owner_at_closure.py')]]
record=dict(status='RUNNING',started_utc=datetime.now(timezone.utc).isoformat(),commands=[],
    failed_original_sequence_sha256=sha(HERE/'policy-and-restoration-execution-0001.json'),corrected_policy_verification_sha256=sha(HERE/'device-local-assets-policy-adjacent-0001-verified.json'),
    scope='All actual policy tests and saved originals already PASS. Only report checker handling was repaired using exact unchanged E3 schemas and independent post-phase known50-file owner guard. Two legacy reports omit individual owner hashes; one omits network metadata. No synthetic additions, product/test/APK edits or retroactive failed-sequence rewrite. This continuation restores development0056/consent original and captures actual final source/known owner paths. F1 closure/checkpoint still required.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
note=f'M4F1 at {record["started_utc"]}: approved-policy core three methods/13 cases passes588.185s; adjacent three methods/13 retained cases passes210.053s and all originals are saved. First checker raises KeyError because two unchanged legacy policy reports omit per-method owner hashes, and SourceDetailsPolicy omits network metadata. Original failed sequence/source/stderr stay immutable. Strict schema/source binding plus an actual known50-file post-phase guard before any restoration passes; corrected verification and13-case parity pass without any app/test/APK/original edits. Development31-case parity also passes. No per-method owner guard is invented for legacy omissions. Fresh restoration0056 consent/final source/owner checks are RUNNING under the separate recovery sequence; F1 closure/checkpoint remains held, F2 not started. Whole-session registry preservation is still false; models/other49 files remain protected; mobile data stays on.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;head,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(head+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
for i,argv in enumerate(commands):
    started=datetime.now(timezone.utc).isoformat();print('F1 recovery stage',i,'START',flush=True)
    with (HERE/f'policy-recovery-0001-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'policy-recovery-0001-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=err)
    record['commands'].append(dict(argv=argv,started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),returncode=result.returncode))
    record['status']='FAIL' if result.returncode else 'RUNNING';target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'Hold F1; preserve failure before any progression';print('F1 recovery stage',i,'PASS',flush=True)
record.update(status='PASS_F1_LEGACY_POLICY_VERIFICATION_RECOVERY_RESTORATION_AND_FINAL_GUARDS_NOT_CLOSURE',finished_utc=datetime.now(timezone.utc).isoformat())
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'],flush=True)
