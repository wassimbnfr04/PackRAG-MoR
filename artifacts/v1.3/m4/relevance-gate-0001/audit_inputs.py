"""D1 source/result/history audit; not complete physical acceptance."""
import hashlib,json,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];M4=ROOT/'artifacts/v1.3/m4';HERE=Path(__file__).resolve().parent
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def check(values):
    for name,expected in values.items():assert digest(ROOT/name)==expected,name
out=HERE/'prephone-audit.json';assert not out.exists()
regression=read(M4/'run-0008/result-manifest.json');assert regression['status']=='PASS' and regression['totals']==dict(tests=737,failures=0,errors=0,skipped=0)
runtime={k:v for k,v in regression['source_sha256'].items() if k not in ('PLAN.md','STATUS.md','DECISIONS.md')};check(runtime)
assert len(runtime)==155
desktop={}
for folder,filename,count in [('smoke-0007','smoke-results.json',14),('conflict-smoke-0004','conflict-smoke-results.json',7),('relevance-smoke-0001','relevance-smoke-results.json',4)]:
    result=read(M4/folder/filename);assert result['status']=='PASS' and len(result['cases'])==count
    assert read(M4/folder/'inputs.json')['source_sha256']==runtime
    desktop[folder]=dict(cases=count,sha256=digest(M4/folder/filename))
android=[];apks={}
native='361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef'
for folder,variant in [('build-0014','debug'),('build-0015','demo')]:
    assert read(M4/folder/'build-result.json')['exit_code']==0
    assert read(M4/folder/'host-test-summary.json')['test_methods']==27
    values=read(M4/folder/'source-at-build-start.json')['files'];check(values);android.append(values)
    apks[folder]={p.name:digest(p) for p in (M4/folder).glob('*.apk')}
    with zipfile.ZipFile(M4/folder/f'app-{variant}.apk') as archive:
        assert hashlib.sha256(archive.read('lib/arm64-v8a/libpackrag_jni.so')).hexdigest()==native
assert android[0]==android[1] and len(android[0])==475
historical=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];check(historical);assert len(historical)==587
prior=read(M4/'conflict-gate-0001/gate.json');check(prior['output_sha256'])
reference=read(M4/'relevance-references-0003/reference-provenance.json');check(reference['history_sha256'])
inspection=read(M4/'demo-apk-inspection-0008/inspection.json');assert inspection['status']=='PASS' and inspection['no_internet'] and inspection['native_sha256']==native
assert inspection['apk_sha256']==apks['build-0015']['app-demo.apk']
record=dict(status='PASS_SOURCE_DESKTOP_HISTORY_AUDIT_NOT_COMPLETE_PHYSICAL_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    runtime_inputs=len(runtime),android_inputs_per_variant=len(android[0]),python_tests=737,host_methods_per_variant=27,
    historical_unchanged=len(historical),prior_conflict_saved_outputs_unchanged=len(prior['output_sha256']),
    unchanged_reference_source_identities=len(reference['history_sha256']),runtime_sha256=runtime,android_sha256=android[0],apk_sha256=apks,
    native_sha256=native,desktop=desktop,script_sha256=digest(Path(__file__)))
out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:record[k] for k in ('status','runtime_inputs','android_inputs_per_variant','prior_conflict_saved_outputs_unchanged','historical_unchanged')}))
