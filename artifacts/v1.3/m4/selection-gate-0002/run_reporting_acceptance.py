"""Sequential physical gates with original collection before every APK switch."""
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
prior=read(M4/'device-production-representations-0002/instrumentation-manifest.json')
names=list(read(M4/'device-production-representations-0002/collected-results.json')['saved_sha256'])+['m4-selection-tokenizer.json','m4-selection-runtime.json','m4-selection-guards.json']
assert len(names)==len(set(names))==25
python=[sys.executable,'-X','utf8'];focused=M4/'device-selection-reporter-0001';policy=M4/'device-production-selection-0001';restore=M4/'device-development-restore-0010'
commands=[
    python+[str(HERE/'reporting_delta_proof.py'),'--build-only'],
    python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0030'),'--run',str(focused),'--class-name','org.packrag.product.SelectionDeviceTest','--result-file','m4-selection-runtime.json','--timeout','1800'],
    python+['-m','scripts.v13_collect_phone_results','--run',str(focused),'--files','m4-selection-tokenizer.json,m4-selection-runtime.json,m4-selection-guards.json'],
    python+[str(HERE/'verify_selection.py'),'--run',str(focused),'--target',str(HERE/'reporter-selection-parity.json')],
    python+[str(HERE/'reporting_delta_proof.py')],
    python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0031'),'--run',str(policy),'--class-name','org.packrag.product.SelectionDeviceTest,'+prior['class_name'],'--result-file','m4-selection-runtime.json','--timeout','4500','--variant','demo'],
    python+['-m','scripts.v13_collect_phone_results','--run',str(policy),'--files',','.join(names)],
    python+[str(HERE/'verify_selection.py'),'--run',str(policy),'--target',str(HERE/'policy-selection-parity.json')],
    python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0030'),'--run',str(restore),'--class-name','org.packrag.product.PackImportConsentTest','--result-file','m3-import-consent.json','--timeout','300'],
    python+['-m','scripts.v13_collect_phone_results','--run',str(restore),'--files','m3-import-consent.json'],
    python+[str(HERE/'verify_and_record_reporting.py'),'--check-only'],
]
record=HERE/'reporting-acceptance-execution.json';assert not record.exists();records=[]
for index,command in enumerate(commands):
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat());print('reporting acceptance stage',index,'START',flush=True)
    with (HERE/f'reporting-stage-{index}.stdout.txt').open('xb') as out,(HERE/f'reporting-stage-{index}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());records.append(row)
    record.write_text(json.dumps(dict(status='FAIL' if result.returncode else 'RUNNING',commands=records),indent=2)+'\n')
    assert result.returncode==0,'Stop progression and preserve failed originals before repair'
    print('reporting acceptance stage',index,'PASS',flush=True)
record.write_text(json.dumps(dict(status='PASS_ACCEPTANCE_PREFLIGHT_NOT_CLOSURE_OR_COMPLETE_PRODUCT',commands=records),indent=2)+'\n')
