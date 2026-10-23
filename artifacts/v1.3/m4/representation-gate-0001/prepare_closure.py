"""Adapt every retained D1 acceptance check and add explicit D2 checks."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
old=ROOT/'artifacts/v1.3/m4/relevance-gate-0001/verify_and_record.py'
source=old.read_text(encoding='utf-8')
def replace(before,after):
    global source
    assert before in source,before
    source=source.replace(before,after)
replace('"""Fail-closed D1 closure retaining all bounded conflict/XML gates; D2/D3 remain."""',
    '"""Fail-closed D2 closure retaining D1/security and new representation gates."""')
replace('ROOT = Path(__file__).resolve().parents[4]\nHERE', 'ROOT = Path(__file__).resolve().parents[4]\nsys.path.insert(0,str(ROOT))\nHERE')
for before,after in [('run-0008','run-0009'),('smoke-0007','smoke-0009'),('build-0014','build-0018'),('build-0015','build-0019'),
    ('conflict-smoke-0004','conflict-smoke-0005'),('relevance-smoke-0001','relevance-smoke-0002'),
    ('device-production-relevance-0001','device-production-representations-0001'),('device-relevance-0001','device-representations-0001'),
    ('device-development-restore-0008','device-development-restore-0009'),('demo-apk-inspection-0008','demo-apk-inspection-0009'),
    ('dict(tests=737','dict(tests=792'),('python_tests=737','python_tests=792'),('== 27','== 28'),('host_methods_per_variant=27','host_methods_per_variant=28'),
    ('("build-0018", 24,','("build-0018", 26,'),('("build-0019", 19,','("build-0019", 21,'),
    ('M4D1_RELEVANCE_FUSED_CAP_VERIFIED_NOT_COMPLETE_D_M4_OR_PRODUCT','M4D2_REPRESENTATIONS_VERIFIED_NOT_COMPLETE_D_M4_OR_PRODUCT'),
    ('ALL_D1_ACCEPTANCE_CHECKS_PASS_NO_CLOSURE_RECORD_WRITTEN','ALL_D2_ACCEPTANCE_CHECKS_PASS_NO_CLOSURE_RECORD_WRITTEN')]:replace(before,after)
replace('COMMON = COMMON + ["m4-relevance.json", "m4-relevance-runtime.json"]',
    'COMMON = COMMON + ["m4-relevance.json", "m4-relevance-runtime.json", "m4-representations.json", "m4-representation-runtime.json"]')
replace('prior_conflict=read(M4 / "conflict-gate-0001/gate.json")',
    'prior_relevance=read(M4 / "relevance-gate-0001/gate.json");check_inputs(prior_relevance["output_sha256"])\n    prior_conflict=read(M4 / "conflict-gate-0001/gate.json")')
replace('assert len(runtime)==155','assert set(runtime)=={p.relative_to(ROOT).as_posix() for p in __import__("scripts.v13_result_manifest",fromlist=["public_source_files"]).public_source_files(ROOT)}')
replace('assert len(builds["build-0018"])==475','assert len(builds["build-0018"])>475\n    assert read(M4 / "build-0018/source-at-build-start.json")["scope"]=="ANDROID_PRODUCT_BUILD_CONFIG_SHARED_HOST_FIXTURES_AT_BUILD_START"')
start=source.index('    intermediate=read(');end=source.index('    for recovery,status',start)
source=source[:start]+source[end:]
replace('"device-conflicts-0001" if run_name=="device-representations-0001" else "device-production-conflicts-0001"',
    '"device-relevance-0001" if run_name=="device-representations-0001" else "device-production-relevance-0001"')
replace('"org.packrag.product.RelevanceDeviceTest,"+prior_manifest["class_name"]',
    '"org.packrag.product.RepresentationDeviceTest,"+prior_manifest["class_name"]')
new_checks='''    representation_fixture=M4 / "representation-fixtures-0001"
    rep=read(representation_fixture / "cases.json")
    assert len(rep["packs"])==20 and len(rep["cases"])==14 and len(rep["invalid_cases"])==6
    assert digest(ROOT / "scripts/v13_representation_fixtures.py")==rep["script_sha256"]
    assert digest(ROOT / "scripts/v13_query_identifier_fixtures.py")==rep["builder_sha256"]
    for filename,key in [("embedding-inputs.json","embedding_inputs_sha256"),("source-specifications.json","source_specifications_sha256"),("public-key.raw","public_key_sha256")]:
        assert digest(representation_fixture / filename)==rep[key]
    assert digest(ROOT / "product/tests/fixtures/representation-contracts.json")==rep["fixed_contract_sha256"]
    for row in rep["packs"]:assert digest(representation_fixture / row["filename"])==row["sha256"]
    for build_name,variant in [("build-0018","debug"),("build-0019","demo")]:
        with zipfile.ZipFile(M4 / build_name / f"app-{variant}-androidTest.apk") as archive:
            for path in (ROOT / "product/android/app/src/androidTest/assets/representation-corpus").iterdir():
                assert hashlib.sha256(archive.read("assets/representation-corpus/"+path.name)).hexdigest()==digest(path)
    representation_desktop=read(M4 / "representation-smoke-0002/representation-smoke-results.json")
    assert representation_desktop["status"]=="PASS" and len(representation_desktop["cases"])==8 and representation_desktop["tokenizer_cases"]==14
    rep_inputs=read(M4 / "representation-smoke-0002/inputs.json")["source_sha256"]
    check_inputs(rep_inputs);assert rep_inputs==runtime
    rep_tokens=read(M4 / "representation-smoke-0002/tokenizer-cases.json")
    assert rep_tokens["status"]=="PASS" and len(rep_tokens["cases"])==14
    rep_token_oracle={r["id"]:r for r in rep_tokens["cases"]}
    rep_runtime_oracle={r["id"]:r for r in representation_desktop["cases"]}
    independent=read(M4 / "representation-token-oracle-0002/oracle.json")
    assert independent["status"]=="PASS" and len(independent["cases"])==7
    assert {r["id"] for r in independent["cases"]}=={k for k,v in rep_token_oracle.items() if v["admission"]=="READY"}
    for row in independent["cases"]:
        expected=rep_token_oracle[row["id"]]["actual_tokenizer"]
        assert row["status"]=="PASS" and row["tokens"]==expected["tokens"]
        assert row["prefill_tokens"]==expected["prefill_tokens"] and row["evidence_tokens"]==expected["evidence_tokens"]
    for name,value in read(M4 / "representation-token-oracle-0002/output-hashes.json").items():
        assert digest(M4 / "representation-token-oracle-0002" / name)==value
    partial=M4 / "representation-intermediate-parity-0001"
    assert read(partial / "partial-parity.json")["original_adb_bytes_sha256"]==digest(partial / "m4-representations.json")
    assert read(partial / "runtime-parity.json")["original_adb_bytes_sha256"]==digest(partial / "m4-representation-runtime.json")
    recovery=read(M4 / "build-0017/source-recovery/recovery.json")
    assert recovery["status"]=="PASS_HASH_EXACT_SINGLE_IMPORT_RECONSTRUCTION_NOT_ORIGINAL_BUILD_START_COPY"
    assert digest(M4 / "build-0017/source-recovery/RepresentationDeviceTest.kt")==recovery["reconstructed_sha256"]
    assert recovery["reconstructed_sha256"]==read(M4 / "build-0017/source-at-build-start.json")["files"][recovery["source"]]
'''
replace('    phone = {}',new_checks+'    phone = {}')
extra='''        if "m4-representations.json" in names:
            result=read(run / "m4-representations.json")
            assert result["fixed_contract_cases"]==32 and result["signed_packs"]==20 and len(result["retrieval_cases"])==14
            assert {r["id"] for r in result["invalid_imports"]}==set(rep["invalid_cases"])
            assert len(result["invalid_imports"])==6 and all(not r["accepted"] for r in result["invalid_imports"])
            for row in result["retrieval_cases"]:
                expected=rep_token_oracle[row["id"]]
                assert row["status"]=="PASS" and row["max_embedding_abs_error"]<=1e-4 and row["max_dense_cosine_error"]<=1e-4
                assert row["admission"]==expected["admission"] and row["actual_tokenizer"]==expected["actual_tokenizer"]
                if row["admission"]=="READY":assert row["representations"]==expected["representations"]
            actual=read(run / "m4-representation-runtime.json");assert actual["status"]=="PASS" and len(actual["cases"])==8
            for row in actual["cases"]:
                expected=rep_runtime_oracle[row["id"]];final=expected["result"]
                assert row["status"]==expected["status"]=="PASS" and row["state"]==final["state"]
                assert row["actual_weight_inference"]==expected["actual_weight_inference"]
                if row["actual_weight_inference"]:
                    assert row["state"]=="ANSWER_ACCEPTED" and "74" in row["answer"] and "</think>" not in row["answer"]
                    assert row["prefill_tokens"]==final["token_budget"]["prefill"] and row["evidence_tokens"]==final["token_budget"]["evidence"]
                    assert row["selected"]==[item["chunk_id"] for item in final["selected"]]
                    assert row["sources"]==[{k:s[k] for k in ("id","canonical_text","canonical_language","canonical_text_sha256","generator_representation")} for s in final["sources"]]
                else:assert row["answer"] is None and not row["sources"] and not row["selected"] and row["prefill_tokens"]==row["emitted_tokens_including_terminal"]==0
'''
replace('        phone[run_name] = dict(',extra+'        phone[run_name] = dict(')
start=source.index('    roots = [');end=source.index('    blocked = ',start)
source=source[:start]+'''    roots = [M4 / name for name in ["run-0009","smoke-0009","build-0018","build-0019","build-0017","build-0016","conflict-smoke-0005","relevance-smoke-0002","representation-smoke-0001","representation-smoke-0002","representation-fixtures-0001","demo-apk-inspection-0009","representation-unit-0001","representation-adjacent-0001","representation-adjacent-0002",*PHONE]]
'''+source[end:]
replace('"docs/v1.3/M4D1_RELEVANCE_METHODS.md", "docs/architecture-compliance-matrix.md",',
    '"docs/v1.3/M4D1_RELEVANCE_METHODS.md", "docs/v1.3/M4D2_REPRESENTATION_METHODS.md", "docs/v1.3/M4D3_SELECTION_FREEZE_AUDIT.md", "docs/architecture-compliance-matrix.md",')
replace('relevance_fixed_cases=32,',
    'representation_fixed_cases=32, signed_representation_packs=20, rejected_representation_imports=6, representation_tokenizer_cases=14, actual_representation_runtime_cases=8,\n        prior_relevance_gate_sha256=digest(M4 / "relevance-gate-0001/gate.json"),prior_relevance_outputs_unchanged=len(prior_relevance["output_sha256"]),\n        representation_scope=dict(paragraphs=[401,403,404,546,548],canonical_bytes_preserved=True,synthetic_review_labels_not_real_review=True,remaining="D3 selection/freezing; E UI; F assets; M5-M8"),\n        relevance_fixed_cases=32,')
replace('D2 representations; D3 selection/freezing; E UI; F assets; M5-M8 release/calibration/benchmarks/signing/physical acceptance','D3 selection/freezing; E UI; F assets; M5-M8 release/calibration/benchmarks/signing/physical acceptance')
replace('D2 representations/D3 selection;', 'D3 selection;')
replace('D2/D3/M4E-F/M5-M8 incomplete','D3/M4E-F/M5-M8 incomplete')
replace('"run-0009","smoke-0009"','"run-0009","smoke-0008","smoke-0009"')
replace('"representation-adjacent-0002",*PHONE]', '"representation-adjacent-0002","representation-intermediate-parity-0001","representation-token-oracle-0001","representation-token-oracle-0002",*PHONE]')
target=HERE/'verify_and_record.py';assert not target.exists();target.write_text(source,encoding='utf-8')
(HERE/'closure-derivation.json').write_text(json.dumps(dict(status='PREPARED_NOT_ACCEPTANCE',old_script_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),
    new_script_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),purpose='All retained D1 checks plus D2 fixture/tokenizer/runtime/provenance and expanded host-source identity gates'),indent=2)+'\n',encoding='utf-8')
print('Prepared retained D1 plus D2 closure; not acceptance')
