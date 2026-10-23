"""Versioned F1 device phase. Capture all method originals before any APK switch."""
import argparse,hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);parser.add_argument('--run',required=True)
parser.add_argument('--variant',choices=['debug','demo'],required=True);parser.add_argument('--phase',choices=['core','adjacent'],required=True)
args=parser.parse_args();build=M4/args.build;run=M4/args.run
assert build.parent==M4 and run.parent==M4 and not run.exists()
target=HERE/(args.run+'-execution.json');assert not target.exists()
assert read(build/'build-result.json')['status']=='BUILD_AND_HOST_TESTS_PASS_NOT_DEVICE_ACCEPTANCE'
assert read(build/'build-result.json')['variant']==args.variant
sources=read(build/'source-at-build-start.json')['files']
for name,value in sources.items():assert sha(ROOT/name)==value,name
suites=[ET.parse(p).getroot() for p in (build/'host-tests').rglob('TEST-*.xml')]
totals={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ['tests','failures','errors','skipped']}
assert totals==dict(tests=62,failures=0,errors=0,skipped=0)
if args.phase=='core':
    classes=['LocalAssetReadinessDeviceTest'];files=['m4-local-assets-negative.json','m4-local-assets-runtime.json','m4-local-assets-viewmodel.json']
elif args.variant=='debug':
    classes=['DiagnosticRuntimeDeviceTest','DiagnosticLifecycleDeviceTest','QueryControlsDeviceTest','SourceDetailsViewModelTest']
    files=['m4-diagnostic-runtime.json','m4-diagnostic-lifecycle.json','m4-ui-query-inputs.json','m4-ui-query-runtime.json','m4-source-details-viewmodel.json']
else:
    classes=['DiagnosticPolicyDeviceTest','QueryControlsPolicyTest','SourceDetailsPolicyTest']
    files=['m4-diagnostic-policy.json','m4-ui-query-policy.json','m4-source-details-policy.json']
commands=[
    [sys.executable,'-X','utf8','-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(build),'--run',str(run),
     '--class-name',','.join('org.packrag.product.'+name for name in classes),'--result-file',files[0],'--timeout','3600','--variant',args.variant],
    [sys.executable,'-X','utf8','-m','scripts.v13_collect_phone_results','--run',str(run),'--files',','.join(files)]]
record=dict(status='RUNNING',phase=args.phase,variant=args.variant,build=args.build,run=args.run,android_inputs=len(sources),host_totals=totals,commands=[])
for i,command in enumerate(commands):
    print(args.run,'stage',i,'START',flush=True);start=datetime.now(timezone.utc).isoformat()
    with (HERE/(args.run+f'-stage-{i}.stdout.txt')).open('xb') as out,(HERE/(args.run+f'-stage-{i}.stderr.txt')).open('xb') as err:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
    record['commands'].append(dict(argv=command,started_utc=start,finished_utc=datetime.now(timezone.utc).isoformat(),returncode=result.returncode))
    record['status']='FAIL' if result.returncode else 'RUNNING';target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'Hold F1 and later increments; preserve failure and any passing originals before repair'
    print(args.run,'stage',i,'PASS',flush=True)
saved=read(run/'collected-results.json');assert set(saved['saved_sha256'])==set(files)
for name,value in saved['saved_sha256'].items():assert sha(run/'original-adb'/name)==value and read(run/name)==read(run/'original-adb'/name)
record.update(status='PASS_F1_'+args.phase.upper()+'_ACTUAL_ORIGINALS_NOT_FULL_F1',original_sha256=saved['saved_sha256'],
    instrumentation_sha256=sha(run/'instrumentation-manifest.json'),collection_sha256=sha(run/'collected-results.json'))
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'],flush=True)
