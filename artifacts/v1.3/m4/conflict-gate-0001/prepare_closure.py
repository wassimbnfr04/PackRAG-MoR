"""Prepare adapted fail-closed closure; no runtime source changes or acceptance claims."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'source-metadata-gate-0001'
failure=HERE/'PREPARATION_FAILURE.json'
if not failure.exists():
    failure.write_text(json.dumps(dict(status='PREPARATION_FAILURE_NOT_PRODUCT_FAILURE', reason='First in-memory adapter used overlapping tests=618 and python_tests=618 replacements. Assertion failed before scripts or closure results were written. Repaired by specific tokens.', outputs_written=False),indent=2)+'\n')
s=(PRIOR/'verify_and_record.py').read_text()
replacements={
 'bounded authenticated source-metadata increment':'bounded conflict/XML increment',
 'COMMON = [':'COMMON = ["m4-conflicts.json", ',
 'device-source-metadata-0001':'device-conflicts-0001',
 'device-production-source-metadata-0001':'device-production-conflicts-0001',
 'device-development-restore-0006':'device-development-restore-0007',
 'build-0009':'build-0012','build-0010':'build-0013',
 '20, COMMON + [':'22, COMMON + ["m4-conflict-runtime.json", ',
 '15, COMMON + [':'17, COMMON + ["m4-conflict-runtime.json", ',
 'run-0005':'run-0007','smoke-0005':'smoke-0006',
 'dict(tests=618,':'dict(tests=691,','python_tests=618':'python_tests=691',
 '== 24':'== 26','host_methods_per_variant=24':'host_methods_per_variant=26',
 'demo-apk-inspection-0006':'demo-apk-inspection-0007',
 'ALL_C2A_ACCEPTANCE_CHECKS_PASS':'ALL_C2B_ACCEPTANCE_CHECKS_PASS',
 'M4C2A_SOURCE_METADATA_VERIFIED_NOT_CONFLICT_RESOLUTION_OR_PRODUCT_COMPLETE':'M4C2B_CONFLICT_XML_VERIFIED_NOT_COMPLETE_M4_OR_PRODUCT',
 'C2b rank convention, comparability, conflict-scoped preference and ambiguity policy; E source-screen presentation':'E source-screen presentation remains pending; bounded C2b is separately checked below',
 'Conflict-scoped authority C2 and source-screen presentation E remain pending; whole paragraph not declared verified':'Bounded C2b conflict checks pass separately; E presentation and complete paragraph remain pending',
 'M4C2b/D–F/M5–M8 incomplete':'M4D–F/M5–M8 incomplete',
}
for old,new in replacements.items():
    assert old in s,old
    s=s.replace(old,new)
s=s.replace('    builds, apk_hashes = {}, {}','    prior_metadata=read(M4 / "source-metadata-gate-0001/gate.json")\n    check_inputs(prior_metadata["output_sha256"])\n    builds, apk_hashes = {}, {}')
extra='''    conflict_fixture=M4 / "conflict-fixtures-0001"
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
    conflict_desktop=read(M4 / "conflict-smoke-0003/conflict-smoke-results.json")
    assert conflict_desktop["status"]=="PASS" and len(conflict_desktop["cases"])==7
    conflict_inputs=read(M4 / "conflict-smoke-0003/inputs.json")["source_sha256"]
    check_inputs(conflict_inputs); assert conflict_inputs==runtime
    token_cases=read(M4 / "conflict-smoke-0003/tokenizer-cases.json")
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
    for build_name, variant in [("build-0012", "debug"), ("build-0013", "demo")]:
        with zipfile.ZipFile(M4 / build_name / f"app-{variant}-androidTest.apk") as archive:
            for path in (asset_root / "conflict-corpus").iterdir():
                assert hashlib.sha256(archive.read("assets/conflict-corpus/"+path.name)).hexdigest()==digest(path)
            assert hashlib.sha256(archive.read("assets/prompt-v13-xml-corpus/prompt-reference.json")).hexdigest()==digest(xml_root / "prompt-reference.json")
    audit=read(M4 / "conflict-input-audit-0001/audit.json")
    assert audit["status"]=="PASS_SOURCE_ARTIFACT_AUDIT_NOT_COMPLETE_PHYSICAL_ACCEPTANCE"
    assert len(runtime)==audit["runtime_inputs"]==143
    assert len(builds["build-0012"])==audit["android_inputs_per_variant"]==458
    for recovery,status in [("conflict-source-recovery-0001","PASS_HASH_EXACT_RECONSTRUCTION"),("xml-prompt-source-recovery-0001","PASS_HASH_EXACT_PRE_XML_SOURCE_RECONSTRUCTION")]:
        record=read(M4 / recovery / "recovery.json"); assert record["status"]==status
        for row in record["files"]:
            assert digest(M4 / recovery / row.get("path",row.get("filename")))==row["sha256"]
'''
s=s.replace('    phone = {}\n',extra+'    phone = {}\n')
s=s.replace('r"Time:\\s*([0-9]+[.,][0-9]+)"','r"Time:\\s*([0-9][0-9\\s\\u00a0\\u202f]*[.,][0-9]+)"')
s=s.replace('float(match[1].replace(",", "."))','float(re.sub(r"\\s", "", match[1]).replace(",", "."))')
s=s.replace('    assert read(M4 / "demo-apk-inspection-0007/inspection.json")["status"] == "PASS"','    inspection=read(M4 / "demo-apk-inspection-0007/inspection.json")\n    assert inspection["status"]=="PASS" and inspection["no_internet"]\n    assert inspection["apk_sha256"]==apk_hashes["build-0013"]["app-demo.apk"]\n    assert inspection["native_sha256"]==native_hash\n    assert inspection["approved_store_sha256"]==digest(ROOT / "product/config/release-trust.json")')
s=s.replace('        text = (run / "instrumentation.txt").read_text(encoding="utf-8")','        prior_run="device-source-metadata-0001" if run_name=="device-conflicts-0001" else "device-production-source-metadata-0001" if run_name=="device-production-conflicts-0001" else None\n        if prior_run:\n            prior_manifest=read(M4 / prior_run / "instrumentation-manifest.json")\n            assert manifest["class_name"]=="org.packrag.product.ConflictDeviceTest,org.packrag.product.ConflictRuntimeDeviceTest,"+prior_manifest["class_name"]\n        for selected in manifest["selected_test_sources"].values():\n            assert builds[build_name][selected["source"]]==selected["source_sha256"]\n        text = (run / "instrumentation.txt").read_text(encoding="utf-8")')
phone_extra='''        if "m4-conflicts.json" in names:
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
'''
s=s.replace('        if "m4-source-metadata.json" in names:',phone_extra+'        if "m4-source-metadata.json" in names:')
s=s.replace('"source-metadata-input-audit-0001", *PHONE]','"source-metadata-input-audit-0001", "conflict-fixtures-0001", "conflict-unit-0001", "conflict-adjacent-0001", "conflict-adjacent-0002", "run-0006", "build-0011", "conflict-smoke-0001", "conflict-smoke-0002", "conflict-diagnostic-0001", "conflict-diagnostic-0002", "conflict-smoke-0003", "xml-prompt-unit-0001", "xml-prompt-fixtures-0001", "conflict-source-recovery-0001", "xml-prompt-source-recovery-0001", "conflict-input-audit-0001", *PHONE]')
s=s.replace('"docs/v1.3/M4C2_DESIGN_AUDIT.md",','"docs/v1.3/M4C2_DESIGN_AUDIT.md", "docs/v1.3/M4C2b_CONFLICT_METHODS.md",')
s=s.replace('"docs/v1.3/M4C2b_CONFLICT_METHODS.md",','"docs/v1.3/M4C2b_CONFLICT_METHODS.md", "docs/v1.3/M4D_EVIDENCE_PREPARATION.md",')
s=s.replace('        source_metadata_cases=8,','        conflict_fixed_cases=40, signed_conflict_packs=19, conflict_retrieval_cases=19, actual_conflict_runtime_cases=7, xml_token_parity_cases=10,\n        prior_metadata_gate_sha256=digest(M4 / "source-metadata-gate-0001/gate.json"),\n        prior_metadata_saved_output_identities_unchanged=len(prior_metadata["output_sha256"]),\n        conflict_scope=dict(paragraphs=[519,540,548], adr_sha256=digest(ROOT / "docs/adr/ADR-002-v13-conflict-scope.md"), remaining="D relevance/selection/local fused cap; E UI; F resources; release packs/calibration/PackBench/final physical acceptance"),\n        source_metadata_cases=8,')
s=s.replace('    documents = [','    for path in list(HERE.glob("*.py"))+[HERE / "PREPARATION_FAILURE.json", HERE / "prephone-audit.json", M4 / "conflict-temp-0001/fixture-execution.txt"]:\n        outputs[path.relative_to(ROOT).as_posix()]=digest(path)\n    documents = [')
s=s.replace('        limits=[','        limits=["Authority and relationship metadata are authenticated publisher assertions, not legal truth or general natural-language conflict detection",\n        "Zero-generation guards exclude prefill/emission, not model loading; actual initialization is separately recorded",\n        "XML correction preserves original failed outputs, validator, model, system role and decoding; current acceptance is separately versioned",\n')
(HERE/'verify_and_record.py').write_text(s,encoding='utf-8',newline='\n')
c=(PRIOR/'collect_results.py').read_text().replace('validity-gate-0001','source-metadata-gate-0001')
c=c.replace('names = prior["phone"][args.prior_run]["saved_results"]','names = prior["phone"][args.prior_run]["saved_results"] + ["m4-conflict-runtime.json"]')
(HERE/'collect_results.py').write_text(c,encoding='utf-8',newline='\n')
compile(s,str(HERE/'verify_and_record.py'),'exec'); compile(c,str(HERE/'collect_results.py'),'exec')
print('CLOSURE_SCRIPTS_PREPARED_NOT_ACCEPTANCE')
