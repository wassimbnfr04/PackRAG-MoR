"""Only after completed full suites/originals and before-ADB old-path orchestration failure."""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
target=HERE/'full-background-recovered-execution.json';assert not target.exists()
failed=read(HERE/'full-background-execution.json');assert failed['status']=='FAIL' and len(failed['commands'])==5
assert all(r['returncode']==0 for r in failed['commands'][:4]) and failed['commands'][4]['returncode']!=0
stderr=(HERE/'full-background-stage-4.stderr.txt').read_text(encoding='utf-8')
assert 'FileExistsError' in stderr and 'device-development-restore-0014' in stderr
old=read(HERE/'restoration-path-collision-preparation.json')
for n,v in old['old_e2_public_outputs_guard'].items():assert sha(ROOT/n)==v,n
for run,count in [('device-diagnostics-full-0001',37),('device-diagnostics-policy-full-0001',30)]:
    p=M4/run;manifest=read(p/'instrumentation-manifest.json');saved=read(p/'collected-results.json')
    assert manifest['status']==saved['status']=='PASS' and len(saved['saved_sha256'])==count
    assert f'OK ({count} tests)' in (p/'instrumentation.txt').read_text(encoding='utf-8')
    for n,v in saved['saved_sha256'].items():assert sha(p/'original-adb'/n)==v and read(p/n)==read(p/'original-adb'/n)
sources=read(M4/'build-0052/source-at-build-start.json')['files'];assert sources==read(M4/'build-0053/source-at-build-start.json')['files']
for n,v in sources.items():assert sha(ROOT/n)==v,n
run=M4/'device-development-restore-0015';assert not run.exists();records=[];python=[sys.executable,'-X','utf8']
commands=[python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0052'),'--run',str(run),
    '--class-name','org.packrag.product.PackImportConsentTest','--result-file','m3-import-consent.json','--timeout','300'],
    python+['-m','scripts.v13_collect_phone_results','--run',str(run),'--files','m3-import-consent.json']]
for i,argv in enumerate(commands):
    row=dict(argv=argv,started_utc=datetime.now(timezone.utc).isoformat());print('Fresh restoration',i,'START',flush=True)
    with (HERE/f'restoration-recovery-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'restoration-recovery-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records,prior_orchestration_failure_sha256=sha(HERE/'full-background-execution.json')),indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'Restoration recovery failed; preserve and hold later milestones'
    print('Fresh restoration',i,'PASS',flush=True)
for n,v in old['old_e2_public_outputs_guard'].items():assert sha(ROOT/n)==v,n
target.write_text(json.dumps(dict(status='PASS_E3_FULL_DEVELOPMENT_POLICY_RESTORATION_ORIGINALS_NOT_PARITY_OR_CLOSURE',commands=records,
    successful_prior_commands=failed['commands'][:4],prior_orchestration_failure_sha256=sha(HERE/'full-background-execution.json'),
    scope='New0052 consent0015/restoration originals after actual successful0052 full37 and0053 full30. Old0014 collision fails before any ADB command and remains FAIL; historical0014 unchanged. No full suite rerun or old result promotion.'),indent=2)+'\n',encoding='utf-8')
print('Actual full37/full30/fresh restore0015 originals complete, parity/closure pending')
