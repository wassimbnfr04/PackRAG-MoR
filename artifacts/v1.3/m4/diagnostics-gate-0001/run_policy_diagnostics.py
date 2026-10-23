"""Actual compiled production-policy diagnostic flow, then exact originals. Stop on failure."""
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(HERE/'policy-diagnostics-preflight.json')['status']=='PASS_E3_MATCHED_POLICY_PAIR_NOT_ACTUAL_POLICY_OR_FULL_E3'
target=HERE/'policy-diagnostics-execution.json';assert not target.exists();records=[]
python=[sys.executable,'-X','utf8'];run=M4/'device-diagnostic-policy-0001'
commands=[python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0049'),
    '--run',str(run),'--class-name','org.packrag.product.DiagnosticPolicyDeviceTest','--result-file','m4-diagnostic-policy.json','--timeout','900','--variant','demo'],
    python+['-m','scripts.v13_collect_phone_results','--run',str(run),'--files','m4-diagnostic-policy.json']]
for i,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('E3 policy diagnostic',i,'START',flush=True)
    with (HERE/f'policy-diagnostics-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'policy-diagnostics-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'Hold full gates and preserve original failure; never collect stale phone JSON as new PASS'
    print('E3 policy diagnostic',i,'PASS',flush=True)
value=read(run/'original-adb/m4-diagnostic-policy.json')
assert value['status']=='PASS' and len(value['cases'])==8 and all(r['passed'] for r in value['cases'])
assert value['compiled_developer_mode'] is False and value['actual_weight_inference'] and value['build_type']=='demo'
target.write_text(json.dumps(dict(status='PASS_E3_ACTUAL_COMPILED_POLICY_DIAGNOSTICS_ORIGINAL_NOT_COMPLETE_E3',commands=records),indent=2)+'\n',encoding='utf-8')
