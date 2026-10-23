"""Bounded final-source/desktop/history audit; not physical acceptance."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;M4=ROOT/'artifacts/v1.3/m4'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def check(values):
    for name,expected in values.items():assert digest(ROOT/name)==expected,name
target=HERE/'prephone-audit.json';assert not target.exists()
python=read(M4/'run-0009/result-manifest.json');assert python['status']=='PASS' and python['totals']==dict(tests=792,failures=0,errors=0,skipped=0)
runtime={k:v for k,v in python['source_sha256'].items() if k not in ('PLAN.md','STATUS.md','DECISIONS.md')};check(runtime)
gates={}
for name,filename,count in [('smoke-0009','smoke-results.json',14),('conflict-smoke-0005','conflict-smoke-results.json',7),('relevance-smoke-0002','relevance-smoke-results.json',4),('representation-smoke-0002','representation-smoke-results.json',8)]:
    results=read(M4/name/filename);assert results['status']=='PASS' and len(results['cases'])==count
    assert read(M4/name/'inputs.json')['source_sha256']==runtime
    gates[name]=dict(result_sha256=digest(M4/name/filename),runtime_cases=count)
android={}
for name in ('build-0018','build-0019'):
    identity=read(M4/name/'source-at-build-start.json');assert identity['scope']=='ANDROID_PRODUCT_BUILD_CONFIG_SHARED_HOST_FIXTURES_AT_BUILD_START'
    assert read(M4/name/'build-result.json')['exit_code']==0 and read(M4/name/'host-test-summary.json')['test_methods']==28
    check(identity['files']);android[name]=identity['files']
assert android['build-0018']==android['build-0019']
history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];check(history)
prior=read(M4/'relevance-gate-0001/gate.json');check(prior['output_sha256'])
assert digest(ROOT/'FULL DOCUMENTATION.md')=='7c68e26003dc2debfbe4de9ce79467953fec5268c59947b93b2f2c01d612dbca'
target.write_text(json.dumps(dict(status='PASS_SOURCE_DESKTOP_HISTORY_AUDIT_NOT_COMPLETE_PHYSICAL_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    note='Named prephone audit for closure compatibility; recorded after desktop/build completion while physical instrumentation may already be running. Not a claim that this record preceded installation.',
    runtime_sha256=runtime,android_sha256=android['build-0018'],desktop=gates,historical_unchanged=len(history),prior_d1_saved_outputs_unchanged=len(prior['output_sha256'])),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='PASS',runtime_inputs=len(runtime),android_inputs=len(android['build-0018']),historical=len(history),prior_d1_outputs=len(prior['output_sha256']))))
