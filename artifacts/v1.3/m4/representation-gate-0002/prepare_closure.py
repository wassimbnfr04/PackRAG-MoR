"""Prepare repaired D2 closure without executing or accepting any gate."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;M4=ROOT/'artifacts/v1.3/m4'
old=M4/'representation-gate-0001/verify_and_record.py';source=old.read_text(encoding='utf-8')
def replace(before,after):
    global source
    assert before in source,before
    source=source.replace(before,after)
for before,after in [('run-0009','run-0010'),('smoke-0009','smoke-0010'),('build-0018','build-0020'),('build-0019','build-0021'),
    ('conflict-smoke-0005','conflict-smoke-0006'),('relevance-smoke-0002','relevance-smoke-0003'),('representation-smoke-0002','representation-smoke-0003'),
    ('device-production-representations-0001','device-production-representations-0002'),('device-representations-0001','device-representations-0002'),
    ('demo-apk-inspection-0009','demo-apk-inspection-0010'),('dict(tests=792','dict(tests=954'),('python_tests=792','python_tests=954'),
    ('["test_methods"] == 28','["test_methods"] == 29'),('host_methods_per_variant=28','host_methods_per_variant=29'),('("build-0020", 26,','("build-0020", 27,'),('("build-0021", 21,','("build-0021", 22,')]:replace(before,after)
replace('"m4-representations.json", "m4-representation-runtime.json"]','"m4-representations.json", "m4-representation-runtime.json", "m4-source-text.json"]')
replace('"device-relevance-0001" if run_name=="device-representations-0002" else "device-production-relevance-0001"',
    '"device-representations-0001" if run_name=="device-representations-0002" else "device-production-representations-0001"')
replace('"org.packrag.product.RepresentationDeviceTest,"+prior_manifest["class_name"]','"org.packrag.product.SourceTextDeviceTest,"+prior_manifest["class_name"]')
extra='''    initial=read(HERE / "initial-output-guard.json");check_inputs(initial["files"])
    before=read(M4 / "representation-whitespace-audit-0001/audit.json")
    after=read(M4 / "representation-whitespace-audit-0002/audit.json")
    assert before["status"]=="OBSERVED_PARITY_MISMATCH_D2_ACCEPTANCE_HELD" and len(before["mismatches"])==1 and before["mismatches"][0]["point"]==133
    assert after["status"]=="PASS_NO_MISMATCH" and not after["mismatches"] and len(after["cases"])==29
    presence_fixture=M4 / "source-text-fixtures-0001";presence=read(presence_fixture / "cases.json")
    assert len(presence["packs"])==6 and sum(r["accept"] for r in presence["packs"])==2
    for name,key in [("source-specifications.json","source_specifications_sha256"),("embedding-inputs.json","embedding_inputs_sha256"),("public-key.raw","public_key_sha256")]:assert digest(presence_fixture / name)==presence[key]
    for name,key in [("scripts/v13_source_text_fixtures.py","script_sha256"),("scripts/v13_query_identifier_fixtures.py","builder_sha256"),("scripts/v13_representation_fixtures.py","rendering_helper_sha256"),("product/tests/fixtures/source-text-contracts.json","fixed_contract_sha256")]:assert digest(ROOT / name)==presence[key]
    for row in presence["packs"]:assert digest(presence_fixture / row["filename"])==row["sha256"]
    for build_name,variant in [("build-0020","debug"),("build-0021","demo")]:
        with zipfile.ZipFile(M4 / build_name / f"app-{variant}-androidTest.apk") as archive:
            for path in (ROOT / "product/android/app/src/androidTest/assets/source-text-corpus").iterdir():assert hashlib.sha256(archive.read("assets/source-text-corpus/"+path.name)).hexdigest()==digest(path)
    presence_desktop=read(M4 / "source-text-smoke-0001/source-text-smoke-results.json")
    assert presence_desktop["status"]=="PASS" and len(presence_desktop["imports"])==6 and sum(r["accepted"] for r in presence_desktop["imports"])==2
    presence_inputs=read(M4 / "source-text-smoke-0001/inputs.json")["source_sha256"];check_inputs(presence_inputs);assert presence_inputs==runtime
    presence_token_oracle={r["id"]:r for r in presence_desktop["tokenizer_cases"]};assert len(presence_token_oracle)==2
    for row in presence["packs"]:
        assert next(r for r in presence_desktop["imports"] if r["id"]==row["id"])["accepted"]==row["accept"]
        if row["accept"]:assert presence_token_oracle[row["id"]]["representations"]==[row["generator_representation"]]
'''
replace('    phone = {}',extra+'    phone = {}')
device='''        if "m4-source-text.json" in names:
            result=read(run / "m4-source-text.json")
            assert (result["fixed_presence_cases"],result["whitespace_points"],result["valid_scalars_checked"],result["blank_resolver_checks"])==(38,29,1112064,116)
            assert len(result["imports"])==6 and sum(r["accepted"] for r in result["imports"])==2 and len(result["tokenizer_cases"])==2
            for row in presence["packs"]:assert next(r for r in result["imports"] if r["id"]==row["id"])["accepted"]==row["accept"]
            for row in result["tokenizer_cases"]:
                expected=presence_token_oracle[row["id"]];assert row["status"]=="PASS" and row["max_embedding_abs_error"]<=1e-4
                for key in ("admission","actual_tokenizer","representations","canonical_text","canonical_text_sha256"):assert row[key]==expected[key],(run_name,row["id"],key)
'''
replace('        phone[run_name] = dict(',device+'        phone[run_name] = dict(')
replace('    roots = [M4 / name for name in [','    roots = [M4 / name for name in ["source-text-fixtures-0001","source-text-unit-0001","source-text-smoke-0001","representation-whitespace-audit-0001","representation-whitespace-audit-0002","run-0009","build-0018","build-0019","conflict-smoke-0005","relevance-smoke-0002","representation-smoke-0002","device-representations-0001","device-production-representations-0001","representation-development-parity-0001",')
replace('        representation_fixed_cases=32,','        repaired_presence_scope=dict(fixed_cases=38,whitespace_points=29,valid_scalars_per_platform=1112064,blank_resolver_checks=116,signed_imports=6,rejected_imports=4,actual_tokenizer_positive_cases=2,initial47_phone_outputs="BOUNDED_BASELINE_NOT_REPAIRED_ACCEPTANCE",initial_public_outputs_unchanged=len(initial["files"]),canonical_and_provenance_bytes_preserved=True),\n        representation_fixed_cases=32,')
replace('    for path in list(HERE.glob("*.py"))+list(HERE.glob("*.json")):', '    outputs.update(initial["files"])\n    for path in list(HERE.glob("*.py"))+list(HERE.glob("*.json")):')
replace('"source-text-fixtures-0001","source-text-unit-0001"', '"source-text-intermediate-parity-0001","source-text-fixtures-0001","source-text-unit-0001"')
replace('    blocked = {', '    roots.append(HERE / "preparation-repair")\n    blocked = {')
replace('    roots.append(HERE / "preparation-repair")', '    roots.append(HERE / "preparation-repair")\n    roots.append(ROOT / "artifacts/v1.3/packaging/size-audit-0001")')
replace('documents = ["PLAN.md", "STATUS.md", "DECISIONS.md",', 'documents = ["docs/v1.3/FINAL_DELIVERY_PLAN.md", "PLAN.md", "STATUS.md", "DECISIONS.md",')
replace('    roots.append(ROOT / "artifacts/v1.3/packaging/size-audit-0001")', '    roots.append(ROOT / "artifacts/v1.3/packaging/size-audit-0001")\n    roots.append(M4 / "policy-runtime-observation-0001")')
target=HERE/'verify_and_record.py';assert not target.exists();target.write_text(source,encoding='utf-8')
(HERE/'closure-derivation.json').write_text(json.dumps(dict(status='PREPARED_NOT_ACCEPTANCE',base_script_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),new_script_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),purpose='Retain all initial D2/D1/security checks and add source-text fullscalar/signed/tokenizer repair gates'),indent=2)+'\n',encoding='utf-8')
print('Prepared repaired D2 closure; not acceptance')
