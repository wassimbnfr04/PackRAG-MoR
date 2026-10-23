"""Reproduce narrowly adapted retained D2 checks; never rewrite accepted evidence."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4';BASE=M4/'representation-gate-0002'
names=[('run-0010','run-0012'),('smoke-0010','selection-walking-0002'),('build-0020','build-0028'),('build-0021','build-0029'),
    ('conflict-smoke-0006','conflict-smoke-0007'),('relevance-smoke-0003','relevance-smoke-0004'),('representation-smoke-0003','representation-smoke-0004'),
    ('source-text-smoke-0001','source-text-smoke-0002'),('device-representations-0002','device-selection-full-0001'),
    ('device-production-representations-0002','device-production-selection-0001'),('device-development-restore-0009','device-development-restore-0010'),
    ('demo-apk-inspection-0010','demo-apk-inspection-0011')]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for name in ('verify_and_record.py','prephone_audit.py','inspect_demo.py'):
    original=BASE/name;source=original.read_text();replacements=[]
    def replace(before,after,required=True):
        global source
        count=source.count(before)
        assert count or not required,before
        if count:source=source.replace(before,after);replacements.append(dict(before=before,after=after,count=count))
    for before,after in names:replace(before,after,False)
    replace('tests=954','tests=1010',False)
    # Full anchors: the29 whitespace scalar expectation must remain29.
    replace('["test_methods"] == 29','["test_methods"] == 34',False)
    replace("['test_methods']==29","['test_methods']==34",False)
    if name=='verify_and_record.py':
        replace('27, COMMON','30, COMMON');replace('22, COMMON','25, COMMON')
        replace('"device-representations-0001" if run_name','"device-representations-0002" if run_name')
        replace('else "device-production-representations-0001" if run_name','else "device-production-representations-0002" if run_name')
        replace('"org.packrag.product.SourceTextDeviceTest,"+prior_manifest["class_name"]','"org.packrag.product.SelectionDeviceTest,"+prior_manifest["class_name"]')
        replace('COMMON = COMMON + [','COMMON = ["m4-selection-tokenizer.json","m4-selection-runtime.json","m4-selection-guards.json"] + COMMON + [')
        replace('ALL_D2_ACCEPTANCE_CHECKS_PASS_NO_CLOSURE_RECORD_WRITTEN','ALL_RETAINED_D3_BASELINE_CHECKS_PASS_NO_CLOSURE_RECORD_WRITTEN')
        replace('    target = HERE / "gate.json"','    assert "--check-only" in sys.argv, "Retained adapter cannot write D3 closure"\n    target = HERE / "gate.json"')
        assert 'len(after["cases"])==29' in source
    if name=='inspect_demo.py':replace("'source-text-corpus']","'source-text-corpus','selection-corpus']")
    output=HERE/('retained_checks.py' if name=='verify_and_record.py' else name);assert not output.exists();output.write_text(source,encoding='utf-8')
    records.append(dict(base=str(original.relative_to(ROOT)),base_sha256=digest(original),output=str(output.relative_to(ROOT)),output_sha256=digest(output),replacements=replacements))
guard=HERE/'initial-output-guard.json';assert not guard.exists();guard.write_bytes((BASE/'initial-output-guard.json').read_bytes())
(HERE/'derivation.json').write_text(json.dumps(dict(status='PREPARED_NOT_ACCEPTANCE',preparer_sha256=digest(Path(__file__)),records=records,initial_guard_sha256=digest(guard),
    prior_preparation='gate0001 adapters unexecuted/superseded by phone harness repair; an overly broad29-to34 replacement was found in inspection and avoided here with full anchors'),indent=2)+'\n')
print('RETAINED_ADAPTERS0002_PREPARED_NOT_ACCEPTANCE')
