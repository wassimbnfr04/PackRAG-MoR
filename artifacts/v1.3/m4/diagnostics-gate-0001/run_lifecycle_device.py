"""New actual native/ViewModel lifecycle method and original result collection."""
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(HERE/'lifecycle-preflight.json')['status']=='PASS_E3_LIFECYCLE_HOST_SOURCE_HISTORY_APK_NOT_DEVICE_OR_UI_OR_COMPLETE_E3'
target=HERE/'lifecycle-device-execution.json';assert not target.exists();records=[]
python=[sys.executable,'-X','utf8'];run=M4/'device-diagnostic-lifecycle-0001'
commands=[python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0046'),
    '--run',str(run),'--class-name','org.packrag.product.DiagnosticLifecycleDeviceTest','--result-file','m4-diagnostic-lifecycle.json','--timeout','900'],
    python+['-m','scripts.v13_collect_phone_results','--run',str(run),'--files','m4-diagnostic-lifecycle.json']]
for i,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('E3 lifecycle',i,'START',flush=True)
    with (HERE/f'lifecycle-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'lifecycle-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    target.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'Hold foreground/later E3 gates; preserve failure and diagnose'
    print('E3 lifecycle',i,'PASS',flush=True)
value=read(run/'original-adb/m4-diagnostic-lifecycle.json');assert value['status']=='PASS' and len(value['cases'])==7
assert all(r['passed'] for r in value['cases']) and value['actual_native_replacement_entry'] and value['actual_native_cancel_entry']
target.write_text(json.dumps(dict(status='PASS_E3_REAL_NATIVE_LIFECYCLE_ORIGINAL_NOT_FOREGROUND_OR_COMPLETE_E3',commands=records),indent=2)+'\n',encoding='utf-8')
