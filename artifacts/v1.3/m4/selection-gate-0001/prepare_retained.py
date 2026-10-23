"""Reproduce additive retained checks without rewriting the accepted D2 gate."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
BASE=M4/'representation-gate-0002'
changes=[('run-0010','run-0012'),('smoke-0010','selection-walking-0002'),('build-0020','build-0026'),('build-0021','build-0027'),
    ('conflict-smoke-0006','conflict-smoke-0007'),('relevance-smoke-0003','relevance-smoke-0004'),
    ('representation-smoke-0003','representation-smoke-0004'),('source-text-smoke-0001','source-text-smoke-0002'),
    ('device-representations-0002','device-selection-full-0001'),('device-production-representations-0002','device-production-selection-0001'),
    ('device-development-restore-0009','device-development-restore-0010'),('demo-apk-inspection-0010','demo-apk-inspection-0011'),
    ('tests=954','tests=1010'),('== 29','== 34'),("==29","==34")]
records=[]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in ('verify_and_record.py','prephone_audit.py','inspect_demo.py'):
    original=BASE/name;source=original.read_text();replacements=[]
    for before,after in changes:
        count=source.count(before)
        if count:source=source.replace(before,after);replacements.append(dict(before=before,after=after,count=count))
    if name=='verify_and_record.py':
        source=source.replace('27, COMMON','30, COMMON').replace('22, COMMON','25, COMMON')
        source=source.replace('"device-representations-0001" if run_name','"device-representations-0002" if run_name')
        source=source.replace('else "device-production-representations-0001" if run_name','else "device-production-representations-0002" if run_name')
        source=source.replace('"org.packrag.product.SourceTextDeviceTest,"+prior_manifest["class_name"]','"org.packrag.product.SelectionDeviceTest,"+prior_manifest["class_name"]')
        source=source.replace('COMMON = COMMON + [','COMMON = ["m4-selection-tokenizer.json","m4-selection-runtime.json","m4-selection-guards.json"] + COMMON + [')
        source=source.replace('ALL_D2_ACCEPTANCE_CHECKS_PASS_NO_CLOSURE_RECORD_WRITTEN','ALL_RETAINED_D3_BASELINE_CHECKS_PASS_NO_CLOSURE_RECORD_WRITTEN')
        # This derivative is a retained-check adapter only. A separate additive
        # D3 verifier must bind new selection evidence and write the final gate.
        source=source.replace('    target = HERE / "gate.json"','    assert "--check-only" in sys.argv, "Retained adapter cannot write a D3 closure"\n    target = HERE / "gate.json"')
    if name=='inspect_demo.py':source=source.replace("'source-text-corpus']","'source-text-corpus','selection-corpus']")
    output=HERE/('retained_checks.py' if name=='verify_and_record.py' else name)
    assert not output.exists();output.write_text(source,encoding='utf-8')
    records.append(dict(base=str(original.relative_to(ROOT)),base_sha256=digest(original),output=str(output.relative_to(ROOT)),output_sha256=digest(output),versioned_name_changes=replacements,
        additive_changes='SelectionDeviceTest prefix, three result files, dev30/policy25; adapter restricted to check-only' if name=='verify_and_record.py' else 'Selection corpus excluded from product APK' if name=='inspect_demo.py' else 'Retained full regression/desktop/build source preflight'))
guard=HERE/'initial-output-guard.json';assert not guard.exists();guard.write_bytes((BASE/'initial-output-guard.json').read_bytes())
(HERE/'derivation.json').write_text(json.dumps(dict(status='PREPARED_NOT_ACCEPTANCE',records=records,initial_guard_sha256=digest(guard)),indent=2)+'\n')
print('RETAINED_ADAPTERS_PREPARED_NOT_ACCEPTANCE')
