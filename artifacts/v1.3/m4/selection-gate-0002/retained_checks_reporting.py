"""Fail-closed D2 closure retaining D1/security and new representation gates."""
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
HERE = Path(__file__).resolve().parent
M4 = ROOT / "artifacts/v1.3/m4"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_inputs(values):
    for name, expected in values.items():
        repair=read(HERE / "timing-reporter-repair.json")
        if name==repair["source"] and expected==repair["old_source_sha256"]:
            # Exact single reporting-key delta is proved before entering main.
            assert digest(HERE / "timing-reporter-before.kt")==expected
            assert digest(ROOT / name)==repair["new_source_sha256"]
        else:assert digest(ROOT / name)==expected,name


COMMON = ["m4-conflicts.json", "m4-source-metadata.json", "m4-validity.json", "m4-query-identifiers.json", "m4-query-unicode.json", "m2-generator-prompt-parity.json", "m2-pack-retrieval-parity.json",
          "m3-data-types.json", "m3-extension-names.json", "m3-validation-order.json",
          "m3-residual-security.json", "m3-manifest-schema.json", "m3-database-validation.json",
          "m3-archive-validation.json"]
COMMON = ["m4-selection-tokenizer.json","m4-selection-runtime.json","m4-selection-guards.json"] + COMMON + ["m4-relevance.json", "m4-relevance-runtime.json", "m4-representations.json", "m4-representation-runtime.json", "m4-source-text.json"]
PHONE = {
    "device-selection-full-0002": ("build-0028", 30, COMMON + ["m4-conflict-runtime.json", "m4-query-identifier-runtime.json","m2-generator-cancellation.json",
        "product-runtime-smoke.json", "m3-explicit-lifecycle.json", "m3-atomic-registry.json",
        "m3-process-death.json", "m3-import-consent.json"]),
    "device-production-selection-0001": ("build-0031", 25, COMMON + ["m4-conflict-runtime.json", 
        "m3-production-policy.json", "m3-release-trust-core.json"]),
    "device-development-restore-0010": ("build-0030", 1, ["m3-import-consent.json"]),
}


def main():
    from reporting_delta_proof import prove
    prove(require_device=True)
    assert "--check-only" in sys.argv, "Retained adapter cannot write D3 closure"
    target = HERE / "gate.json"
    architecture_hash=digest(ROOT / "artifacts/v1.3/architecture/architecture-v1.3.docx")
    assert architecture_hash=="9b02f83b186a5b7f0101add861c6ecb40f5eb0b13016f50fa0c76efc6de07536"
    assert not target.exists(), "Gate outputs are immutable"
    python = read(M4 / "run-0012/result-manifest.json")
    assert python["status"] == "PASS" and python["totals"] == dict(tests=1010, failures=0, errors=0, skipped=0)
    # Durable live state is deliberately updated as acceptance proceeds.
    runtime = {k: v for k, v in python["source_sha256"].items() if k not in ("PLAN.md", "STATUS.md", "DECISIONS.md")}
    check_inputs(runtime)
    desktop = read(M4 / "selection-walking-0002/smoke-results.json")
    assert desktop["status"] == "PASS" and len(desktop["cases"]) == 14
    desktop_inputs = read(M4 / "selection-walking-0002/inputs.json")["source_sha256"]
    check_inputs(desktop_inputs)
    assert runtime == desktop_inputs
    historical = read(ROOT / "artifacts/v1.3/m0/historical-evidence-guard.json")["files"]
    check_inputs(historical)
    prior_relevance=read(M4 / "relevance-gate-0001/gate.json");check_inputs(prior_relevance["output_sha256"])
    prior_conflict=read(M4 / "conflict-gate-0001/gate.json")
    check_inputs(prior_conflict["output_sha256"])
    prior_query = read(M4 / "query-gate-0001/gate.json")
    check_inputs(prior_query["output_sha256"])
    prior_validity=read(M4 / "validity-gate-0001/gate.json")
    check_inputs(prior_validity["output_sha256"])
    prior_metadata=read(M4 / "source-metadata-gate-0001/gate.json")
    check_inputs(prior_metadata["output_sha256"])
    builds, apk_hashes = {}, {}
    native_hash = "361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef"
    for name, variant in [("build-0028", "debug"), ("build-0029", "demo"), ("build-0030", "debug"), ("build-0031", "demo")]:
        build = M4 / name
        assert read(build / "build-result.json")["exit_code"] == 0
        assert read(build / "host-test-summary.json")["test_methods"] == 34
        xmls = list((build / "host-tests").rglob("TEST-*.xml")); assert xmls
        for path in xmls:
            suite = ET.parse(path).getroot()
            assert int(suite.attrib.get("failures", 0)) == int(suite.attrib.get("errors", 0)) == 0
        inputs = read(build / "source-at-build-start.json")["files"]
        check_inputs(inputs); builds[name] = inputs
        apk = build / f"app-{variant}.apk"
        with zipfile.ZipFile(apk) as archive:
            assert hashlib.sha256(archive.read("lib/arm64-v8a/libpackrag_jni.so")).hexdigest() == native_hash
        apk_hashes[name] = {p.name: digest(p) for p in build.glob("*.apk")}
    assert builds["build-0028"] == builds["build-0029"]
    fixture = M4 / "source-metadata-fixtures-0003"
    fixture_record = read(fixture / "cases.json")
    assert digest(ROOT / "scripts/v13_source_metadata_fixtures.py") == fixture_record["script_sha256"]
    assert digest(fixture / "embedding-inputs.json") == fixture_record["embedding_inputs_sha256"]
    assert digest(fixture / "source-metadata.kpack") == fixture_record["pack_sha256"]
    assert digest(fixture / "public-key.raw") == fixture_record["public_key_sha256"]
    for build_name, variant in [("build-0028", "debug"), ("build-0029", "demo")]:
        with zipfile.ZipFile(M4 / build_name / f"app-{variant}-androidTest.apk") as archive:
            for name in ("cases.json", "source-metadata.kpack", "public-key.raw"):
                assert hashlib.sha256(archive.read("assets/source-metadata-corpus/" + name)).hexdigest() == digest(fixture / name)
    conflict_fixture=M4 / "conflict-fixtures-0001"
    cf=read(conflict_fixture / "cases.json")
    assert digest(ROOT / "scripts/v13_conflict_fixtures.py")==cf["script_sha256"]
    assert digest(conflict_fixture / "embedding-inputs.json")==cf["embedding_inputs_sha256"]
    assert digest(conflict_fixture / "source-specifications.json")==cf["source_specifications_sha256"]
    assert digest(ROOT / "product/tests/fixtures/conflict-contracts.json")==cf["shared_contract_sha256"]
    assert len(cf["packs"])==len(cf["cases"])==19
    for pack in cf["packs"]:
        assert digest(conflict_fixture / pack["filename"])==pack["sha256"]
    for key in cf["public_keys"]:
        assert digest(conflict_fixture / key["filename"])==key["sha256"]
    conflict_desktop=read(M4 / "conflict-smoke-0007/conflict-smoke-results.json")
    assert conflict_desktop["status"]=="PASS" and len(conflict_desktop["cases"])==7
    conflict_inputs=read(M4 / "conflict-smoke-0007/inputs.json")["source_sha256"]
    check_inputs(conflict_inputs); assert conflict_inputs==runtime
    token_cases=read(M4 / "conflict-smoke-0007/tokenizer-cases.json")
    assert token_cases["status"]=="PASS" and len(token_cases["cases"])==19
    xml_root=M4 / "xml-prompt-fixtures-0001"
    xml_ref=read(xml_root / "prompt-reference.json")
    assert digest(ROOT / "scripts/v13_xml_prompt_fixtures.py")==xml_ref["script_sha256"]
    assert len(xml_ref["prompt_cases"])==10 and xml_ref["policy_text_unchanged"]
    assert xml_ref["prompt_serialization"]=="V1.3_XML_ENVELOPE"
    asset_root=ROOT / "product/android/app/src/androidTest/assets"
    for row in cf["packs"]+cf["public_keys"]:
        assert digest(asset_root / "conflict-corpus" / row["filename"])==row["sha256"]
    assert digest(asset_root / "conflict-corpus/cases.json")==digest(conflict_fixture / "cases.json")
    assert digest(asset_root / "conflict-corpus/conflict-contracts.json")==cf["shared_contract_sha256"]
    for name,value in xml_ref["original_assets_sha256"].items():
        assert digest(asset_root / name)==value
    for build_name, variant in [("build-0028", "debug"), ("build-0029", "demo")]:
        with zipfile.ZipFile(M4 / build_name / f"app-{variant}-androidTest.apk") as archive:
            for path in (asset_root / "conflict-corpus").iterdir():
                assert hashlib.sha256(archive.read("assets/conflict-corpus/"+path.name)).hexdigest()==digest(path)
            assert hashlib.sha256(archive.read("assets/prompt-v13-xml-corpus/prompt-reference.json")).hexdigest()==digest(xml_root / "prompt-reference.json")
    audit=read(M4 / "conflict-input-audit-0001/audit.json")
    assert audit["status"]=="PASS_SOURCE_ARTIFACT_AUDIT_NOT_COMPLETE_PHYSICAL_ACCEPTANCE"
    assert set(runtime)=={p.relative_to(ROOT).as_posix() for p in __import__("scripts.v13_result_manifest",fromlist=["public_source_files"]).public_source_files(ROOT)}
    assert len(builds["build-0028"])>475
    assert read(M4 / "build-0028/source-at-build-start.json")["scope"]=="ANDROID_PRODUCT_BUILD_CONFIG_SHARED_HOST_FIXTURES_AT_BUILD_START"
    current_audit=read(HERE / "prephone-audit.json")
    assert current_audit["status"]=="PASS_SOURCE_DESKTOP_HISTORY_AUDIT_NOT_COMPLETE_PHYSICAL_ACCEPTANCE"
    assert current_audit["runtime_sha256"]==runtime and current_audit["android_sha256"]==builds["build-0028"]
    for recovery,status in [("conflict-source-recovery-0001","PASS_HASH_EXACT_RECONSTRUCTION"),("xml-prompt-source-recovery-0001","PASS_HASH_EXACT_PRE_XML_SOURCE_RECONSTRUCTION")]:
        record=read(M4 / recovery / "recovery.json"); assert record["status"]==status
        for row in record["files"]:
            assert digest(M4 / recovery / row.get("path",row.get("filename")))==row["sha256"]
    new_fixture=M4 / "relevance-fixtures-0001"
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
    for build_name,variant in [("build-0028","debug"),("build-0029","demo")]:
        with zipfile.ZipFile(M4 / build_name / f"app-{variant}-androidTest.apk") as archive:
            for namespace in ("relevance-corpus","relevance-reference-corpus"):
                for path in (ROOT / "product/android/app/src/androidTest/assets" / namespace).iterdir():
                    assert hashlib.sha256(archive.read("assets/"+namespace+"/"+path.name)).hexdigest()==digest(path)
    relevant_desktop=read(M4 / "relevance-smoke-0004/relevance-smoke-results.json")
    assert relevant_desktop["status"]=="PASS" and len(relevant_desktop["cases"])==4 and relevant_desktop["tokenizer_cases"]==8
    relevant_inputs=read(M4 / "relevance-smoke-0004/inputs.json")["source_sha256"]
    check_inputs(relevant_inputs);assert relevant_inputs==runtime
    relevant_tokens=read(M4 / "relevance-smoke-0004/tokenizer-cases.json")
    assert relevant_tokens["status"]=="PASS" and len(relevant_tokens["cases"])==8
    relevant_token_oracle={r["id"]:r for r in relevant_tokens["cases"]}
    relevant_runtime_oracle={r["id"]:r for r in relevant_desktop["cases"]}
    representation_fixture=M4 / "representation-fixtures-0001"
    rep=read(representation_fixture / "cases.json")
    assert len(rep["packs"])==20 and len(rep["cases"])==14 and len(rep["invalid_cases"])==6
    assert digest(ROOT / "scripts/v13_representation_fixtures.py")==rep["script_sha256"]
    assert digest(ROOT / "scripts/v13_query_identifier_fixtures.py")==rep["builder_sha256"]
    for filename,key in [("embedding-inputs.json","embedding_inputs_sha256"),("source-specifications.json","source_specifications_sha256"),("public-key.raw","public_key_sha256")]:
        assert digest(representation_fixture / filename)==rep[key]
    assert digest(ROOT / "product/tests/fixtures/representation-contracts.json")==rep["fixed_contract_sha256"]
    for row in rep["packs"]:assert digest(representation_fixture / row["filename"])==row["sha256"]
    for build_name,variant in [("build-0028","debug"),("build-0029","demo")]:
        with zipfile.ZipFile(M4 / build_name / f"app-{variant}-androidTest.apk") as archive:
            for path in (ROOT / "product/android/app/src/androidTest/assets/representation-corpus").iterdir():
                assert hashlib.sha256(archive.read("assets/representation-corpus/"+path.name)).hexdigest()==digest(path)
    representation_desktop=read(M4 / "representation-smoke-0004/representation-smoke-results.json")
    assert representation_desktop["status"]=="PASS" and len(representation_desktop["cases"])==8 and representation_desktop["tokenizer_cases"]==14
    rep_inputs=read(M4 / "representation-smoke-0004/inputs.json")["source_sha256"]
    check_inputs(rep_inputs);assert rep_inputs==runtime
    rep_tokens=read(M4 / "representation-smoke-0004/tokenizer-cases.json")
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
    initial=read(HERE / "initial-output-guard.json");check_inputs(initial["files"])
    before=read(M4 / "representation-whitespace-audit-0001/audit.json")
    after=read(M4 / "representation-whitespace-audit-0002/audit.json")
    assert before["status"]=="OBSERVED_PARITY_MISMATCH_D2_ACCEPTANCE_HELD" and len(before["mismatches"])==1 and before["mismatches"][0]["point"]==133
    assert after["status"]=="PASS_NO_MISMATCH" and not after["mismatches"] and len(after["cases"])==29
    presence_fixture=M4 / "source-text-fixtures-0001";presence=read(presence_fixture / "cases.json")
    assert len(presence["packs"])==6 and sum(r["accept"] for r in presence["packs"])==2
    for name,key in [("source-specifications.json","source_specifications_sha256"),("embedding-inputs.json","embedding_inputs_sha256"),("public-key.raw","public_key_sha256")]:assert digest(presence_fixture / name)==presence[key]
    for name,key in [("scripts/v13_source_text_fixtures.py","script_sha256"),("scripts/v13_query_identifier_fixtures.py","builder_sha256"),("scripts/v13_representation_fixtures.py","rendering_helper_sha256"),("product/tests/fixtures/source-text-contracts.json","fixed_contract_sha256")]:assert digest(ROOT / name)==presence[key]
    for row in presence["packs"]:assert digest(presence_fixture / row["filename"])==row["sha256"]
    for build_name,variant in [("build-0028","debug"),("build-0029","demo")]:
        with zipfile.ZipFile(M4 / build_name / f"app-{variant}-androidTest.apk") as archive:
            for path in (ROOT / "product/android/app/src/androidTest/assets/source-text-corpus").iterdir():assert hashlib.sha256(archive.read("assets/source-text-corpus/"+path.name)).hexdigest()==digest(path)
    presence_desktop=read(M4 / "source-text-smoke-0002/source-text-smoke-results.json")
    assert presence_desktop["status"]=="PASS" and len(presence_desktop["imports"])==6 and sum(r["accepted"] for r in presence_desktop["imports"])==2
    presence_inputs=read(M4 / "source-text-smoke-0002/inputs.json")["source_sha256"];check_inputs(presence_inputs);assert presence_inputs==runtime
    presence_token_oracle={r["id"]:r for r in presence_desktop["tokenizer_cases"]};assert len(presence_token_oracle)==2
    for row in presence["packs"]:
        assert next(r for r in presence_desktop["imports"] if r["id"]==row["id"])["accepted"]==row["accept"]
        if row["accept"]:assert presence_token_oracle[row["id"]]["representations"]==[row["generator_representation"]]
    phone = {}
    for run_name, (build_name, count, names) in PHONE.items():
        run = M4 / run_name
        manifest = read(run / "instrumentation-manifest.json")
        assert manifest["status"] == "PASS" and manifest["apk_sha256"] == apk_hashes[build_name]
        prior_run="device-representations-0002" if run_name=="device-selection-full-0002" else "device-production-representations-0002" if run_name=="device-production-selection-0001" else None
        if prior_run:
            prior_manifest=read(M4 / prior_run / "instrumentation-manifest.json")
            assert manifest["class_name"]=="org.packrag.product.SelectionDeviceTest,"+prior_manifest["class_name"]
        for selected in manifest["selected_test_sources"].values():
            assert builds[build_name][selected["source"]]==selected["source_sha256"]
        text = (run / "instrumentation.txt").read_text(encoding="utf-8")
        noun = "test" if count == 1 else "tests"
        assert f"OK ({count} {noun})" in text and "FAILURES" not in text
        match = re.search(r"Time:\s*([0-9][0-9\s\u00a0\u202f]*[.,][0-9]+)", text); assert match
        for name in names:
            assert read(run / name)["status"] == "PASS", (run_name, name)
        if "m4-conflicts.json" in names:
            result=read(run / "m4-conflicts.json")
            assert result["fixed_contract_cases"]==40 and result["signed_packs"]==19
            assert not result["global_authority_sort"] and not result["graph_expansion"]
            assert result["actual_tokenizer_companion_admission"] and len(result["retrieval_cases"])==19
            oracle={row["id"]:row for row in token_cases["cases"]}
            for row in result["retrieval_cases"]:
                assert row["status"]=="PASS" and row["max_embedding_abs_error"]<=1e-4 and row["max_dense_cosine_error"]<=1e-4
                expected=oracle[row["id"]]
                assert row["admission"]==expected["admission"] and row["actual_tokenizer"]==expected["actual_tokenizer"]
            actual=read(run / "m4-conflict-runtime.json")
            assert actual["status"]=="PASS" and len(actual["cases"])==7
            runtime_oracle={row["id"]:row for row in conflict_desktop["cases"]}
            for row in actual["cases"]:
                expected=runtime_oracle[row["id"]]; final=expected["result"]
                assert row["status"]==expected["status"]=="PASS" and row["state"]==final["state"]
                assert row["actual_weight_inference"]==expected["actual_weight_inference"]
                if row["actual_weight_inference"]:
                    assert row["state"]=="ANSWER_ACCEPTED" and "74" in row["answer"] and "68" not in row["answer"]
                    assert row["prefill_tokens"]==final["token_budget"]["prefill"]
                    assert row["evidence_tokens"]==final["token_budget"]["evidence"]
                    assert row["selected"]==[item["chunk_id"] for item in final["selected"]]
                    assert row["prefill_tokens"]<=1536 and row["evidence_tokens"]<=1200 and len(row["selected"])<=4
                    assert row["sources"] and all(item["conflict_states"] for item in row["sources"])
                else:
                    assert row["answer"] is None and not row["selected"] and row["prefill_tokens"]==row["emitted_tokens_including_terminal"]==0
            prompt=read(run / "m2-generator-prompt-parity.json")
            assert prompt["prompt_serialization"]=="V1.3_XML_ENVELOPE" and prompt["normalized_query_embedding"]
        if "m4-source-metadata.json" in names:
            result=read(run / "m4-source-metadata.json")
            assert len(result["metadata_cases"])==8 and result["directed_relations"]==5
            assert not result["authority_sort"] and not result["graph_expansion"]
            assert len(result["retrieval_cases"])==12
            assert all(row["status"]=="PASS" and row["max_embedding_abs_error"]<=1e-4 and row["max_dense_cosine_error"]<=1e-4 for row in result["retrieval_cases"])
        if "m4-validity.json" in names:
            result = read(run / "m4-validity.json")
            assert len(result["contract_cases"]) == 32 and result["fixed_provenance_cases"] == 3
            assert len(result["retrieval_cases"]) == 12 and result["freshness_not_eligibility"]
            assert all(row["status"] == "PASS" and row["max_embedding_abs_error"] <= 1e-4 and row["max_dense_cosine_error"] <= 1e-4 for row in result["retrieval_cases"])
        if "product-runtime-smoke.json" in names:
            assert read(run / "product-runtime-smoke.json")["unknown_open_validity_provenance_checked"]
            assert read(run / "product-runtime-smoke.json")["authenticated_source_metadata_checked"]
        if "m3-release-trust-core.json" in names:
            assert read(run / "m3-release-trust-core.json")["unknown_open_validity_provenance_checked"]
            assert read(run / "m3-release-trust-core.json")["authenticated_source_metadata_checked"]
        if "m4-query-unicode.json" in names:
            result = read(run / "m4-query-unicode.json")
            assert result["official_rows"] == 19074 and result["official_comparisons"] == 95370
            assert len(result["query_cases"]) == 1453
            assert result["table_sha256"] == digest(ROOT / "product/config/query-unicode15.json")
        if "m4-query-identifiers.json" in names:
            result = read(run / "m4-query-identifiers.json")
            assert len(result["query_contract_cases"]) == 28
            assert result["word_cases"] == 5 and result["alias_boundary_cases"] == 11
            assert len(result["retrieval_cases"]) == 10
            assert next(row for row in result["retrieval_cases"] if row["id"]=="AMBIGUITY_BEFORE_LOCAL_CAP")["candidate_count"]==32
            assert all(row["status"] == "PASS" and row["max_embedding_abs_error"] <= 1e-4 and row["max_dense_cosine_error"] <= 1e-4 for row in result["retrieval_cases"])
        if "m4-relevance.json" in names:
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
        if "m4-representations.json" in names:
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
        if "m4-source-text.json" in names:
            result=read(run / "m4-source-text.json")
            assert (result["fixed_presence_cases"],result["whitespace_points"],result["valid_scalars_checked"],result["blank_resolver_checks"])==(38,29,1112064,116)
            assert len(result["imports"])==6 and sum(r["accepted"] for r in result["imports"])==2 and len(result["tokenizer_cases"])==2
            for row in presence["packs"]:assert next(r for r in result["imports"] if r["id"]==row["id"])["accepted"]==row["accept"]
            for row in result["tokenizer_cases"]:
                expected=presence_token_oracle[row["id"]];assert row["status"]=="PASS" and row["max_embedding_abs_error"]<=1e-4
                for key in ("admission","actual_tokenizer","representations","canonical_text","canonical_text_sha256"):assert row[key]==expected[key],(run_name,row["id"],key)
        phone[run_name] = dict(methods=count, whole_instrumentation_seconds=float(re.sub(r"\s", "", match[1]).replace(",", ".")),
                               saved_results=names, apk_sha256=manifest["apk_sha256"])
    inspection=read(M4 / "demo-apk-inspection-0011/inspection.json")
    assert inspection["status"]=="PASS" and inspection["no_internet"]
    assert inspection["apk_sha256"]==apk_hashes["build-0029"]["app-demo.apk"]
    assert inspection["native_sha256"]==native_hash
    assert inspection["approved_store_sha256"]==digest(ROOT / "product/config/release-trust.json")
    official_hash = read(M4 / "unicode15-inputs-0001/acquisition.json")["files"]["NormalizationTest.txt"]["sha256"]
    corpus_files = ["product/tests/unicode15/NormalizationTest.txt",
                    "product/android/app/src/androidTest/assets/unicode15/NormalizationTest.txt"]
    for name in corpus_files:
        assert digest(ROOT / name) == official_hash, name
    for build_name, variant in [("build-0028", "debug"), ("build-0029", "demo")]:
        with zipfile.ZipFile(M4 / build_name / f"app-{variant}-androidTest.apk") as archive:
            assert hashlib.sha256(archive.read("assets/unicode15/NormalizationTest.txt")).hexdigest() == official_hash
    if "--check-only" in sys.argv:
        print("ALL_RETAINED_D3_BASELINE_CHECKS_PASS_NO_CLOSURE_RECORD_WRITTEN")
        return
    roots = [M4 / name for name in ["source-text-intermediate-parity-0001","source-text-fixtures-0001","source-text-unit-0001","source-text-smoke-0002","representation-whitespace-audit-0001","representation-whitespace-audit-0002","run-0009","build-0018","build-0019","conflict-smoke-0005","relevance-smoke-0002","representation-smoke-0002","device-representations-0001","device-production-representations-0001","representation-development-parity-0001","run-0012","smoke-0008","selection-walking-0002","build-0028","build-0029","build-0017","build-0016","conflict-smoke-0007","relevance-smoke-0004","representation-smoke-0001","representation-smoke-0004","representation-fixtures-0001","demo-apk-inspection-0011","representation-unit-0001","representation-adjacent-0001","representation-adjacent-0002","representation-intermediate-parity-0001","representation-token-oracle-0001","representation-token-oracle-0002",*PHONE]]
    roots.append(HERE / "preparation-repair")
    roots.append(ROOT / "artifacts/v1.3/packaging/size-audit-0001")
    roots.append(M4 / "policy-runtime-observation-0001")
    blocked = {"temp", "stage", "pytest-temp", "__pycache__", ".private", "build", ".gradle", ".cxx", ".kotlin"}
    outputs = {}
    for root in roots:
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(ROOT)
            if blocked.intersection(relative.parts) or path.suffix in (".apk", ".pyc", ".class"):
                continue
            assert path.resolve().is_relative_to(ROOT), relative
            if path.is_file():
                outputs[relative.as_posix()] = digest(path)
    outputs.update(initial["files"])
    for path in list(HERE.glob("*.py"))+list(HERE.glob("*.json")):
        outputs[path.relative_to(ROOT).as_posix()]=digest(path)
    documents = ["docs/v1.3/FINAL_DELIVERY_PLAN.md", "PLAN.md", "STATUS.md", "DECISIONS.md", "docs/v1.3/M4_INCREMENT_PLAN.md",
        "docs/v1.3/M4_IMPLEMENTATION_LOG.md", "docs/v1.3/M4B1_UNICODE_METHODS.md", "docs/v1.3/M4C_VALIDITY_CONFLICT_PLAN.md", "docs/v1.3/M4C2a_SOURCE_METADATA_METHODS.md", "docs/v1.3/M4C2_DESIGN_AUDIT.md", "docs/v1.3/M4C2b_CONFLICT_METHODS.md", "docs/v1.3/M4D_EVIDENCE_PREPARATION.md", "docs/v1.3/M4D1_RELEVANCE_METHODS.md", "docs/v1.3/M4D2_REPRESENTATION_METHODS.md", "docs/v1.3/M4D3_SELECTION_FREEZE_AUDIT.md", "docs/architecture-compliance-matrix.md",
        "docs/v1.3/M4D2_REPRESENTATION_AUDIT.md", "product/licenses/Unicode15-LICENSE.txt", "product/licenses/Unicode15-NOTICE.md",
        "docs/adr/ADR-002-v13-conflict-scope.md"]
    documents_at_closure = {}
    for name in documents:
        source = ROOT / name
        snapshot = HERE / "state-snapshot" / name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        assert not snapshot.exists(), snapshot
        snapshot.write_bytes(source.read_bytes())
        documents_at_closure[name] = digest(source)
        outputs[snapshot.relative_to(ROOT).as_posix()] = digest(snapshot)
    for name in corpus_files:
        outputs[name] = digest(ROOT / name)
    correction = ROOT / "artifacts/v1.3/m4/unicode-gate-0001/CORRECTION.md"
    outputs[correction.relative_to(ROOT).as_posix()] = digest(correction)
    outputs[Path(__file__).relative_to(ROOT).as_posix()] = digest(Path(__file__))
    record = dict(status="M4D2_REPRESENTATIONS_VERIFIED_NOT_COMPLETE_D_M4_OR_PRODUCT",
        recorded_utc=datetime.now(timezone.utc).isoformat(), python_tests=1010, host_methods_per_variant=29,
        repaired_presence_scope=dict(fixed_cases=38,whitespace_points=29,valid_scalars_per_platform=1112064,blank_resolver_checks=116,signed_imports=6,rejected_imports=4,actual_tokenizer_positive_cases=2,initial47_phone_outputs="BOUNDED_BASELINE_NOT_REPAIRED_ACCEPTANCE",initial_public_outputs_unchanged=len(initial["files"]),canonical_and_provenance_bytes_preserved=True),
        representation_fixed_cases=32, signed_representation_packs=20, rejected_representation_imports=6, representation_tokenizer_cases=14, actual_representation_runtime_cases=8,
        prior_relevance_gate_sha256=digest(M4 / "relevance-gate-0001/gate.json"),prior_relevance_outputs_unchanged=len(prior_relevance["output_sha256"]),
        representation_scope=dict(paragraphs=[401,403,404,546,548],canonical_bytes_preserved=True,synthetic_review_labels_not_real_review=True,remaining="D3 selection/freezing; E UI; F assets; M5-M8"),
        relevance_fixed_cases=32, signed_relevance_cases=8, actual_relevance_runtime_cases=4,
        relevance_scope=dict(paragraphs=[519,521,532,536,998],remaining="D3 selection/freezing; E UI; F assets; M5-M8 release/calibration/benchmarks/signing/physical acceptance"),
        prior_conflict_gate_sha256=digest(M4 / "conflict-gate-0001/gate.json"),prior_conflict_outputs_unchanged=len(prior_conflict["output_sha256"]),
        official_rows_per_platform=19074, official_comparisons_per_platform=95370, shared_query_cases=1453,
        scalar_reference_comparisons=1112064, historical_identities_unchanged=len(historical),
        conflict_fixed_cases=40, signed_conflict_packs=19, conflict_retrieval_cases=19, actual_conflict_runtime_cases=7, xml_token_parity_cases=10,
        prior_metadata_gate_sha256=digest(M4 / "source-metadata-gate-0001/gate.json"),
        prior_metadata_saved_output_identities_unchanged=len(prior_metadata["output_sha256"]),
        conflict_scope=dict(paragraphs=[519,540,548], adr_sha256=digest(ROOT / "docs/adr/ADR-002-v13-conflict-scope.md"), remaining="D3 selection; E UI; F resources; release packs/calibration/PackBench/final physical acceptance"),
        source_metadata_cases=8, directed_source_relations=5, source_metadata_retrieval_cases=12,
        source_metadata_requirement_scope=dict(architecture_sha256=architecture_hash,
            paragraphs=[390, 392, 397],
            source_paragraph_sha256={str(index): hashlib.sha256(next(row["text"] for row in read(ROOT / "artifacts/v1.3/architecture/paragraphs.json") if row["index"] == index).encode()).hexdigest() for index in (390, 392, 397)},
            scope="Existing authenticated source fields and directed relations preserved in both readers and runtime citation provenance",
            remaining="E source-screen presentation remains pending; bounded C2b is separately checked below"),
        metadata_embedding_inputs_sha256=fixture_record["embedding_inputs_sha256"],
        prior_validity_gate_sha256=digest(M4 / "validity-gate-0001/gate.json"),
        shared_validity_cases=32, fixed_validity_provenance_cases=3, signed_validity_retrieval_cases=12,
        shared_strict_query_cases=28, shared_word_cases=5, shared_alias_boundary_cases=11,
        actual_normalized_granite_retrieval_cases=10, frozen_word_codepoint_checks=1114112,
        prior_query_gate_sha256=digest(M4 / "query-gate-0001/gate.json"),
        unchanged_public_runtime_inputs=len(runtime), frozen_android_inputs_per_variant=len(builds["build-0028"]),
        unicode_table_sha256=digest(ROOT / "product/config/query-unicode15.json"), native_jni_sha256=native_hash,
        apk_sha256=apk_hashes, phone=phone, source_sha256=runtime, android_source_sha256=builds,
        output_sha256=outputs, documents_at_closure=documents_at_closure,
        validity_requirement_scope=dict(architecture_sha256=architecture_hash,
            source_paragraph_sha256=__import__("hashlib").sha256(next(row["text"] for row in read(ROOT / "artifacts/v1.3/architecture/paragraphs.json") if row["index"]==540).encode()).hexdigest(),
            paragraph=540, scope="Source/chunk intersection, exclusive ends, jurisdiction/current-law predicate and original/effective unknown/inherited provenance only",
            remaining="Bounded C2b conflict checks pass separately; E presentation and complete paragraph remain pending"),
        prior_query_saved_output_identities_unchanged=len(prior_query["output_sha256"]),
        prior_validity_saved_output_identities_unchanged=len(prior_validity["output_sha256"]),
        limits=["Authority and relationship metadata are authenticated publisher assertions, not legal truth or general natural-language conflict detection",
        "Zero-generation guards exclude prefill/emission, not model loading; actual initialization is separately recorded",
        "XML correction preserves original failed outputs, validator, model, system role and decoding; current acceptance is separately versioned",
"Generated/exhaustive scalar checks share Python15 oracle; official corpus is independent",
        "One OS-normalizer probe is not an exhaustive OS audit or old-APK execution",
        "Live durable-state hashes record closure time; future authorized state updates are expected",
        "Instrumentable demo is Android Debug signed, not final nondebuggable release",
        "Synthetic functional data is not release calibration, held-out accuracy or source/translation review",
        "Intermediate memory/thermal snapshot and functional timings do not establish performance or causal bottleneck",
        "Mobile data remains on; no airplane isolation acceptance; D3/M4E-F/M5-M8 incomplete"])
    target.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: record[k] for k in ["status", "phone", "unchanged_public_runtime_inputs", "frozen_android_inputs_per_variant"]}, indent=2))


if __name__ == "__main__":
    main()
