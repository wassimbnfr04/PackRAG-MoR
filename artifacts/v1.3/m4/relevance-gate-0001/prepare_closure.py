"""Explicit adapter retaining all prior conflict/security checks and adding D1."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
old=ROOT/'artifacts/v1.3/m4/conflict-gate-0001/verify_and_record.py'
source=old.read_text(encoding='utf-8')
def replace(before,after):
    global source
    assert before in source,before
    source=source.replace(before,after)
for before,after in [('run-0007','run-0008'),('smoke-0006','smoke-0007'),('build-0012','build-0014'),('build-0013','build-0015'),
    ('conflict-smoke-0003','conflict-smoke-0004'),('device-production-conflicts-0001','device-production-relevance-0001'),
    ('device-conflicts-0001','device-relevance-0001'),('device-development-restore-0007','device-development-restore-0008'),
    ('demo-apk-inspection-0007','demo-apk-inspection-0008'),('dict(tests=691','dict(tests=737'),('python_tests=691','python_tests=737'),
    ('== 26','== 27'),('host_methods_per_variant=26','host_methods_per_variant=27'),('("build-0014", 22,','("build-0014", 24,'),
    ('("build-0015", 17,','("build-0015", 19,'),('M4C2B_CONFLICT_XML_VERIFIED_NOT_COMPLETE_M4_OR_PRODUCT','M4D1_RELEVANCE_FUSED_CAP_VERIFIED_NOT_COMPLETE_D_M4_OR_PRODUCT'),
    ('ALL_C2B_ACCEPTANCE_CHECKS_PASS_NO_CLOSURE_RECORD_WRITTEN','ALL_D1_ACCEPTANCE_CHECKS_PASS_NO_CLOSURE_RECORD_WRITTEN')]:replace(before,after)
replace('"device-source-metadata-0001" if run_name=="device-relevance-0001" else "device-production-source-metadata-0001"',
    '"device-conflicts-0001" if run_name=="device-relevance-0001" else "device-production-conflicts-0001"')
replace('"org.packrag.product.ConflictDeviceTest,org.packrag.product.ConflictRuntimeDeviceTest,"+prior_manifest["class_name"]',
    '"org.packrag.product.RelevanceDeviceTest,"+prior_manifest["class_name"]')
replace('assert len(runtime)==audit["runtime_inputs"]==143','assert len(runtime)==155')
replace('assert len(builds["build-0014"])==audit["android_inputs_per_variant"]==458','assert len(builds["build-0014"])==475')
replace('PHONE = {','COMMON = COMMON + ["m4-relevance.json", "m4-relevance-runtime.json"]\nPHONE = {')
replace('prior_query = read(M4 / "query-gate-0001/gate.json")','prior_conflict=read(M4 / "conflict-gate-0001/gate.json")\n    check_inputs(prior_conflict["output_sha256"])\n    prior_query = read(M4 / "query-gate-0001/gate.json")')
new_checks='''    new_fixture=M4 / "relevance-fixtures-0001"
    rf=read(new_fixture / "cases.json")
    assert len(rf["packs"])==len(rf["cases"])==8
    assert digest(ROOT / "scripts/v13_relevance_fixtures.py")==rf["script_sha256"]
    assert digest(ROOT / "scripts/v13_query_identifier_fixtures.py")==rf["builder_script_sha256"]
    for filename,key in [("embedding-inputs.json","embedding_inputs_sha256"),("source-specifications.json","source_specifications_sha256"),("fixed-expectations.json","fixed_expectations_sha256"),("public-key.raw","public_key_sha256")]:
        assert digest(new_fixture / filename)==rf[key]
    assert digest(ROOT / "product/tests/fixtures/relevance-contracts.json")==rf["fixed_gate_sha256"]
    for row in rf["packs"]:assert digest(new_fixture / row["filename"])==row["sha256"]
    migrated=M4 / "relevance-references-0003"
    provenance=read(migrated / "reference-provenance.json");check_inputs(provenance["history_sha256"])
    assert digest(ROOT / "scripts/v13_relevance_references.py")==provenance["script_sha256"]
    assert provenance["gate_sha256"]==digest(M4 / "conflict-gate-0001/gate.json")
    assert [(r["kind"],r["id"],r["old_count"],r["new_count"]) for r in provenance["changes"]]==[("query","AMBIGUITY_BEFORE_LOCAL_CAP",17,32),("conflict","BEFORE_CAP",16,32)]
    for build_name,variant in [("build-0014","debug"),("build-0015","demo")]:
        with zipfile.ZipFile(M4 / build_name / f"app-{variant}-androidTest.apk") as archive:
            for namespace in ("relevance-corpus","relevance-reference-corpus"):
                for path in (ROOT / "product/android/app/src/androidTest/assets" / namespace).iterdir():
                    assert hashlib.sha256(archive.read("assets/"+namespace+"/"+path.name)).hexdigest()==digest(path)
    relevant_desktop=read(M4 / "relevance-smoke-0001/relevance-smoke-results.json")
    assert relevant_desktop["status"]=="PASS" and len(relevant_desktop["cases"])==4 and relevant_desktop["tokenizer_cases"]==8
    relevant_inputs=read(M4 / "relevance-smoke-0001/inputs.json")["source_sha256"]
    check_inputs(relevant_inputs);assert relevant_inputs==runtime
    relevant_tokens=read(M4 / "relevance-smoke-0001/tokenizer-cases.json")
    assert relevant_tokens["status"]=="PASS" and len(relevant_tokens["cases"])==8
    relevant_token_oracle={r["id"]:r for r in relevant_tokens["cases"]}
    relevant_runtime_oracle={r["id"]:r for r in relevant_desktop["cases"]}
'''
replace('    phone = {}',new_checks+'    phone = {}')
extra='''        if "m4-relevance.json" in names:
            result=read(run / "m4-relevance.json")
            assert result["fixed_contract_cases"]==32 and result["signed_packs"]==8 and len(result["retrieval_cases"])==8
            for row in result["retrieval_cases"]:
                expected=relevant_token_oracle[row["id"]]
                assert row["status"]=="PASS" and row["max_embedding_abs_error"]<=1e-4 and row["max_dense_cosine_error"]<=1e-4
                assert row["admission"]==expected["admission"] and row["actual_tokenizer"]==expected["actual_tokenizer"]
            actual=read(run / "m4-relevance-runtime.json");assert actual["status"]=="PASS" and len(actual["cases"])==4
            for row in actual["cases"]:
                expected=relevant_runtime_oracle[row["id"]];final=expected["result"]
                assert row["status"]==expected["status"]=="PASS" and row["state"]==final["state"]
                assert row["actual_weight_inference"]==expected["actual_weight_inference"]
                if row["actual_weight_inference"]:
                    assert row["state"]=="ANSWER_ACCEPTED" and "74" in row["answer"]
                    assert row["prefill_tokens"]==final["token_budget"]["prefill"] and row["evidence_tokens"]==final["token_budget"]["evidence"]
                    assert row["selected"]==[item["chunk_id"] for item in final["selected"]]
                else:assert row["answer"] is None and not row["selected"] and row["prefill_tokens"]==row["emitted_tokens_including_terminal"]==0
            collection=read(run / "collected-results.json");assert collection["status"]=="PASS" and set(collection["saved_sha256"])==set(names)
            for filename,expected in collection["saved_sha256"].items():
                assert digest(run / "original-adb" / filename)==expected
                assert read(run / filename)==read(run / "original-adb" / filename)
'''
replace('        phone[run_name] = dict(',extra+'        phone[run_name] = dict(')
start=source.index('    roots = [');end=source.index('    blocked = ',start)
source=source[:start]+'''    roots = [M4 / name for name in ["run-0008","smoke-0007","build-0014","build-0015","conflict-smoke-0004","relevance-smoke-0001","demo-apk-inspection-0008","relevance-unit-0001","relevance-references-0001","relevance-references-0002","relevance-references-0003","relevance-fixtures-0001",*PHONE]]
'''+source[end:]
replace('list(HERE.glob("*.py"))+[HERE / "PREPARATION_FAILURE.json", HERE / "prephone-audit.json", M4 / "conflict-temp-0001/fixture-execution.txt"]','list(HERE.glob("*.py"))')
replace('"docs/v1.3/M4D_EVIDENCE_PREPARATION.md", "docs/architecture-compliance-matrix.md",','"docs/v1.3/M4D_EVIDENCE_PREPARATION.md", "docs/v1.3/M4D1_RELEVANCE_METHODS.md", "docs/architecture-compliance-matrix.md",')
replace('official_rows_per_platform=19074,','relevance_fixed_cases=32, signed_relevance_cases=8, actual_relevance_runtime_cases=4,\n        relevance_scope=dict(paragraphs=[519,521,532,536,998],remaining="D2 representations; D3 selection/freezing; E UI; F assets; M5-M8 release/calibration/benchmarks/signing/physical acceptance"),\n        prior_conflict_gate_sha256=digest(M4 / "conflict-gate-0001/gate.json"),prior_conflict_outputs_unchanged=len(prior_conflict["output_sha256"]),\n        official_rows_per_platform=19074,')
replace('D relevance/selection/local fused cap; E UI; F resources; release packs/calibration/PackBench/final physical acceptance','D2 representations/D3 selection; E UI; F resources; release packs/calibration/PackBench/final physical acceptance')
replace('Mobile data remains on; no airplane isolation acceptance; M4D–F/M5–M8 incomplete','Mobile data remains on; no airplane isolation acceptance; D2/D3/M4E-F/M5-M8 incomplete')
target=HERE/'verify_and_record.py';assert not target.exists();target.write_text(source,encoding='utf-8')
(HERE/'closure-derivation.json').write_text(json.dumps(dict(status='PREPARED_NOT_ACCEPTANCE',old_script_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),
    new_script_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),purpose='Retained C2b checks plus complete D1 gates; explicit source/count/path changes'),indent=2)+'\n',encoding='utf-8')
print('Prepared source-bound D1 closure adapter, not acceptance')
