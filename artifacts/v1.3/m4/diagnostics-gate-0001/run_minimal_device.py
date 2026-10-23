"""Actual first diagnostic flow; all later E3 changes wait for this scoped result."""
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(HERE/'minimal-preflight.json')['status']=='PASS_E3_MINIMAL_SOURCE_HOST_HISTORY_APK_NOT_DEVICE_OR_E3_ACCEPTANCE'
target=HERE/'minimal-device-execution.json';assert not target.exists();records=[]
python=[sys.executable,'-X','utf8'];run=M4/'device-diagnostics-0001'
commands=[python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0043'),
    '--run',str(run),'--class-name','org.packrag.product.DiagnosticRuntimeDeviceTest','--result-file','m4-diagnostic-runtime.json','--timeout','900'],
    python+['-m','scripts.v13_collect_phone_results','--run',str(run),'--files','m4-diagnostic-runtime.json']]
for i,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('E3 minimal',i,'START',flush=True)
    with (HERE/f'minimal-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'minimal-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'Hold adjacent E3 implementation; preserve failure and diagnose'
    print('E3 minimal',i,'PASS',flush=True)
target.write_text(json.dumps(dict(status='PASS_E3_FIRST_DIAGNOSTIC_RUNTIME_AND_ORIGINAL_NOT_LIFECYCLE_DISPATCH_OR_E3_CLOSURE',commands=records),indent=2)+'\n',encoding='utf-8')
