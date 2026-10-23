"""Repaired inputs and retained outputs audit while full phone gate runs."""
import hashlib,json,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;M4=ROOT/'artifacts/v1.3/m4'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def check(values):
    for name,expected in values.items():assert digest(ROOT/name)==expected,name
target=HERE/'source-start-audit.json';assert not target.exists()
regression=read(M4/'run-0010/result-manifest.json');assert regression['totals']==dict(tests=954,failures=0,errors=0,skipped=0)
runtime={k:v for k,v in regression['source_sha256'].items() if k not in ('PLAN.md','STATUS.md','DECISIONS.md')};check(runtime)
builds={};apk={}
for name,variant in [('build-0020','debug'),('build-0021','demo')]:
    build=M4/name;assert read(build/'build-result.json')['exit_code']==0 and read(build/'host-test-summary.json')['test_methods']==29
    builds[name]=read(build/'source-at-build-start.json')['files'];check(builds[name])
    apk[name]={p.name:digest(p) for p in build.glob('*.apk')}
    with zipfile.ZipFile(build/('app-'+variant+'.apk')) as archive:assert hashlib.sha256(archive.read('lib/arm64-v8a/libpackrag_jni.so')).hexdigest()=='361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef'
assert builds['build-0020']==builds['build-0021']
history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];check(history)
prior=read(M4/'relevance-gate-0001/gate.json')['output_sha256'];check(prior)
initial=read(HERE/'initial-output-guard.json')['files'];check(initial)
target.write_text(json.dumps(dict(status='PASS_INPUT_IDENTITY_AUDIT_NOT_COMPLETE_PHYSICAL_OR_MILESTONE_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),runtime_sha256=runtime,android_sha256=builds['build-0020'],apk_sha256=apk,historical_unchanged=len(history),prior_d1_outputs_unchanged=len(prior),initial_d2_public_outputs_unchanged=len(initial)),indent=2)+'\n')
print(json.dumps(dict(status='PASS',runtime_inputs=len(runtime),android_inputs=len(builds['build-0020']),history=len(history),D1_outputs=len(prior),initial_D2_outputs=len(initial))))
