"""Exact derived adapters; preserve old acceptance preparers and their hashes."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
changes=[]
def replace(text,old,new,count=1):
    assert text.count(old)==count,(old,text.count(old),count)
    changes.append(dict(before=old,after=new,count=count));return text.replace(old,new)
old=HERE/'retained_checks.py';source=old.read_text()
source=replace(source,'def check_inputs(values):\n    for name, expected in values.items():\n        assert digest(ROOT / name) == expected, name',
'''def check_inputs(values):
    for name, expected in values.items():
        repair=read(HERE / "timing-reporter-repair.json")
        if name==repair["source"] and expected==repair["old_source_sha256"]:
            # Exact single reporting-key delta is proved before entering main.
            assert digest(HERE / "timing-reporter-before.kt")==expected
            assert digest(ROOT / name)==repair["new_source_sha256"]
        else:assert digest(ROOT / name)==expected,name''')
source=replace(source,'    assert "--check-only" in sys.argv, "Retained adapter cannot write D3 closure"',
'''    from reporting_delta_proof import prove
    prove(require_device=True)
    assert "--check-only" in sys.argv, "Retained adapter cannot write D3 closure"''')
source=replace(source,'"device-production-selection-0001": ("build-0029", 25','"device-production-selection-0001": ("build-0031", 25')
source=replace(source,'"device-development-restore-0010": ("build-0028", 1','"device-development-restore-0010": ("build-0030", 1')
source=replace(source,'for name, variant in [("build-0028", "debug"), ("build-0029", "demo")]:','for name, variant in [("build-0028", "debug"), ("build-0029", "demo"), ("build-0030", "debug"), ("build-0031", "demo")]:')
target=HERE/'retained_checks_reporting.py';assert not target.exists();target.write_text(source)
records=[dict(base=old.name,base_sha256=digest(old),target=target.name,target_sha256=digest(target),literal_changes=list(changes))]
changes.clear();old=HERE/'verify_and_record.py';source=old.read_text()
source=replace(source,"str(HERE/'retained_checks.py')","str(HERE/'retained_checks_reporting.py')")
source=replace(source,"android=read(M4/'build-0028/source-at-build-start.json')['files'];check(android)","from reporting_delta_proof import prove\n    reuse=prove(require_device=True)\n    android=read(M4/'build-0030/source-at-build-start.json')['files'];check(android)")
source=replace(source,"assert android==read(M4/'build-0029/source-at-build-start.json')['files'] and len(android)==543","assert android==read(M4/'build-0031/source-at-build-start.json')['files'] and len(android)==543")
source=replace(source,"[('build-0028','debug'),('build-0029','demo')]","[('build-0030','debug'),('build-0031','demo')]")
source=replace(source,"('device-production-selection-0001',25,'build-0029')","('device-production-selection-0001',25,'build-0031')")
source=replace(source,"assert read(restored/'instrumentation-manifest.json')['apk_sha256']==phone['device-selection-full-0002']['apk_sha256']","assert read(restored/'instrumentation-manifest.json')['apk_sha256']=={p.name:file_sha(p) for p in (M4/'build-0030').glob('*.apk')}\n    assert read(restored/'instrumentation-manifest.json')['apk_sha256']['app-debug.apk']==phone['device-selection-full-0002']['apk_sha256']['app-debug.apk']")
source=replace(source,"'build-0028','build-0029',","'build-0028','build-0029','build-0030','build-0031',")
source=replace(source,"'device-selection-full-0001','device-selection-full-0002',","'device-selection-full-0001','device-selection-full-0002','device-selection-reporter-0001',")
source=replace(source,'original_model_format_failure_preserved=True,','report_only_bounded_reuse=reuse,original_model_format_failure_preserved=True,')
target=HERE/'verify_and_record_reporting.py';assert not target.exists();target.write_text(source)
records.append(dict(base=old.name,base_sha256=digest(old),target=target.name,target_sha256=digest(target),literal_changes=list(changes)))
target=HERE/'reporting-adapter-derivation.json';assert not target.exists();target.write_text(json.dumps(dict(status='PREPARED_NOT_ACCEPTED',adapters=records),indent=2)+'\n')
print('REPORTING_ADAPTERS_PREPARED_NOT_ACCEPTED')
