"""Preserve collection failure and recovered bytes; fresh restoration run, no relabeling."""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
failed=M4/'device-development-restore-0012'
assert read(failed/'instrumentation-manifest.json')['status']=='FAIL'
assert 'OK (1 test)' in (failed/'instrumentation.txt').read_text(encoding='utf-8')
target=HERE/'restoration-recovery.json';assert not target.exists()
command=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/m3-import-consent.json']
payload=subprocess.run(command,capture_output=True,timeout=30,check=True)
value=json.loads(payload.stdout);assert value['status']=='PASS' and len(value['cases'])==4 and all(r['passed'] for r in value['cases'])
saved=HERE/'restoration-0012-recovered-original.json';assert not saved.exists();saved.write_bytes(payload.stdout)
record=dict(status='RECOVERED_PREVIOUS_COMPLETED_METHOD_BYTES_FRESH_RESTORATION_PENDING_NOT_RELABELLED',
    recorded_utc=datetime.now(timezone.utc).isoformat(),failed_manifest_sha256=sha(failed/'instrumentation-manifest.json'),
    original_instrumentation_sha256=sha(failed/'instrumentation.txt'), recovered_original_sha256=sha(saved),
    command=command,stderr_utf8=payload.stderr.decode('utf-8',errors='replace'),
    failure='Primary result read returned nonzero after successful JUnit; original runner did not save that command stderr, so exact cause is unknown.',commands=[])
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
run=M4/'device-development-restore-0014';python=[sys.executable,'-X','utf8']
commands=[python+['-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(M4/'build-0039'),'--run',str(run),
    '--class-name','org.packrag.product.PackImportConsentTest','--result-file','m3-import-consent.json','--timeout','300'],
    python+['-m','scripts.v13_collect_phone_results','--run',str(run),'--files','m3-import-consent.json']]
for i,command in enumerate(commands):
    print('Restoration retry',i,'START',flush=True)
    row=dict(argv=command,started_utc=datetime.now(timezone.utc).isoformat())
    with (HERE/f'restoration-retry-stage-{i}.stdout.txt').open('xb') as out,(HERE/f'restoration-retry-stage-{i}.stderr.txt').open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
    row.update(returncode=result.returncode,finished_utc=datetime.now(timezone.utc).isoformat());record['commands'].append(row)
    record['status']='FAIL_RETRY_OR_COLLECTION_NOT_RELABELLED' if result.returncode else 'RETRY_RUNNING_NOT_RELABELLED'
    target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');assert result.returncode==0
record['status']='PASS_FRESH_DEVELOPMENT_RESTORATION_ORIGINAL_SAVED_PRIOR_COLLECTION_FAILURE_PRESERVED_NOT_E2_CLOSURE'
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'],flush=True)
