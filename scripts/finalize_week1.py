"""Assemble the evidence index without converting unrun gates into successes."""
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def write(path,value):(ROOT/path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def log_pass(path,marker):return marker in (ROOT/path).read_text(encoding='utf-8',errors='replace')

mor=read('reference/mor/reference_metadata.json')
g0=read('gates/g0/g0_summary.json')
audit=read('export/mor_export_report.json')
phone=read('fallback/smollm2/phone_test_results.json')
conversion=read('fallback/smollm2/conversion/conversion_metadata.json')
pack=read('packs/synthetic-week1/build_provenance.json')
vector=read('tests/signature_vector/expected.json')
assert g0['classification']=='G0_FAIL'
assert not phone['physical_phone'] and not phone['offline_generation']
assert not audit['pin_matches']
assert log_pass('artifacts/week1/logs/kpack_tests_final.log','49 passed')
assert log_pass('artifacts/week1/logs/android_build_verified.log','BUILD SUCCESSFUL')
assert log_pass('artifacts/week1/logs/llamacpp_android_completion_build.log','Linking CXX executable bin\\llama-completion')
unit_path=ROOT/'android/week1-spike/build/test-results/testDebugUnitTest/TEST-org.packrag.week1.SignatureVectorTest.xml'
unit=ET.parse(unit_path).getroot()
assert unit.attrib['tests']=='2' and unit.attrib['failures']=='0' and unit.attrib['errors']=='0'
out=ROOT/'artifacts/week1/android';out.mkdir(parents=True,exist_ok=True)
apks={}
for kind,path in [('app','android/week1-spike/build/outputs/apk/debug/week1-spike-debug.apk'),('instrumentation','android/week1-spike/build/outputs/apk/androidTest/debug/week1-spike-debug-androidTest.apk')]:
    original=ROOT/path;target=out/original.name;shutil.copyfile(original,target)
    with zipfile.ZipFile(target) as archive:
        assert not any('test_private_key' in name for name in archive.namelist())
        if kind=='app':
            assert archive.read('assets/week1.kpack')==(ROOT/'packs/synthetic-week1/org.packrag.synthetic.week1-1.0.0.kpack').read_bytes()
            assert {n.split('/')[1] for n in archive.namelist() if n.startswith('lib/')}=={'arm64-v8a'}
    apks[kind]={'path':str(target.relative_to(ROOT)).replace('\\','/'),'sha256':sha(target),'bytes':target.stat().st_size}
shutil.copyfile(unit_path,out/'jvm_test_results.xml')
android={'status':'BUILD_AND_JVM_PASS_PHYSICAL_TEST_BLOCKED','physical_phone':False,'apk_build':'PASS','jvm_tests':{'passed':2,'total':2,'signature_negative_cases':5,'report':'artifacts/week1/android/jvm_test_results.xml'},'android_signature_verify':None,'android_query':None,'instrumentation_status':'BLOCKED_PENDING_PHONE','apks':apks,'private_fixture_key_in_apk':False,'note':'JVM Tink verification and successful APK compilation do not prove Android-device interoperability.'}
write('artifacts/week1/android/android_verification_results.json',android)
native={}
for name in ['llama-cli','llama-completion']:
    p=ROOT/'fallback/smollm2/android/build-arm64/bin'/name
    native[name]={'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size,'abi':'arm64-v8a','android_platform':'android-28','cross_build':'PASS','phone_executed':False}
write('fallback/smollm2/android/build_metadata.json',{'candidate_commit':conversion['llamacpp_candidate_commit'],'phone_validated_commit':None,'binaries':native,'gguf':conversion['gguf_sha256'],'ndk':'30.0.16248370','cmake':'3.31.1','cpu_only':True,'shared_libraries':False,'openmp':False})
tool_files=['microsoft-jdk-17.0.20.1-windows-x64.zip','gradle-9.6.0-bin.zip','commandlinetools-win-16111833_latest.zip','android-ndk-r30-windows.zip','cmake-3.31.1-windows.zip','platform-37.0_r02.zip','build-tools_r37_windows.zip','platform-tools.zip']
tool_hashes={name:{'sha256':sha(ROOT/'vendor'/name),'bytes':(ROOT/'vendor'/name).stat().st_size} for name in tool_files if (ROOT/'vendor'/name).exists()}
lock={'architecture':'PackRAG-MoR v1.2','status':'REQUIRED_PHONE_AND_PINNED_EXPORT_GATES_UNMET','recorded_at_utc':datetime.now(timezone.utc).isoformat(),'host_environment':'WINDOWS_NATIVE','python':'3.12.13','android':{'jdk':'17.0.20.1+1 Microsoft','gradle':'9.6.0','agp':'9.4.0','kotlin':'2.4.20','kotlin_compiler_jar_sha256':sha(ROOT/'vendor/maven/org/jetbrains/kotlin/kotlin-compiler-embeddable/2.4.20/kotlin-compiler-embeddable-2.4.20.jar'),'ndk':'30.0.16248370','cmake':'3.31.1','min_sdk':28,'compile_sdk':37,'target_sdk':37,'build_tools':'37.0.0','primary_abi':'arm64-v8a','sqlite_bundled':'2.7.1','tink_android':'1.23.0','internet_permission':False},'onnxruntime':{'desktop':'1.30.0','mobile_target':'1.30.0','mobile_embedder_executed':False},'mor':{'repository':'https://github.com/raymin0223/mixture_of_recursions','repo_commit':audit['mor_repository_commit'],'branch':'main','checkpoint_source':'https://drive.google.com/file/d/1rhTvqLiTPVikY-J-TYdXApYQ80X_cq47/view','checkpoint_bytes':mor['checkpoint_bytes'],'checkpoint_sha256':mor['checkpoint_sha256'],'config_sha256':mor['config_sha256'],'training_config_sha256':mor['training_config_sha256'],'tokenizer_sha256':mor['tokenizer_sha256'],'tokenizer_hashes':mor['tokenizer_hashes'],'torch':mor['torch_version'],'torch_commit':mor['torch_commit'],'transformers':'4.52.4','cuda_runtime':'12.4','attention_backend':'eager','precision':'bf16','generation_implementation':'full_prefix_reference'},'executorch':{'version':'1.5.0','source_commit':'f7140a46ff38e919c557d45b102d3ff26097c8c9','android_runtime_commit':None,'pytorch_source_ref':'release/2.14','pytorch_required_commit':audit['pinned_pytorch_commit'],'pytorch_diagnostic_version':audit['actual_pytorch_version'],'pytorch_diagnostic_commit':audit['actual_pytorch_commit'],'pin_matches':False,'diagnostic_substitution_adopted':False,'exact_target_status':'BLOCKED'},'granite':{'model_id':pack['embedding_profile']['model_id'],'revision':pack['embedding_profile']['model_revision'],'embedding_profile':pack['embedding_profile'],'artifact_hashes':pack['input_hashes']},'smollm2':{'model_id':conversion['model_id'],'revision':conversion['model_revision'],'quantization':'F16','gguf_sha256':conversion['gguf_sha256'],'gguf_bytes':conversion['gguf_bytes'],'official_chat_template_preserved':True},'llamacpp':{'repository':'https://github.com/ggml-org/llama.cpp','candidate_commit':conversion['llamacpp_candidate_commit'],'first_successful_target_phone_commit':None,'target_phone_validated':False,'cross_builds':native},'kpack_test_key':{'key_id':vector['key_id'],'warning':'TEST KEY ONLY — NEVER USE FOR RELEASE'},'tool_archive_hashes':tool_hashes,'resolved_python_environments':{name:f'artifacts/week1/environment/requirements-{name}-resolved.txt' for name in ['mor','et15','pack','convert']}}
write('toolchain.lock.json',lock)
blockers=['Target physical phone unavailable: offline SmolLM2 generation, five-case evidence smoke, performance/memory and Android KPack instrumentation are unrun.','Exact ExecuTorch PyTorch source pin is unmet; current export/runtime artifacts are NON_PINNED_PYTORCH_DIAGNOSTIC only.','Diagnostic MoR runtime cannot load aten::sort.values; dynamic routing shape guards fail; explicit cache/decode export and Android numerical parity remain unproven.']
summary={'architecture':'PackRAG-MoR v1.2','week':1,'overall_status':'INCOMPLETE_BLOCKED','mor_reference':{'status':'PASS','deterministic_generation':'PASS','host_environment':'WINDOWS_NATIVE','checkpoint_sha256':mor['checkpoint_sha256'],'repo_commit':audit['mor_repository_commit'],'attention_backend':'eager','generation_implementation':'full_prefix_reference'},'g0':{**g0['categories'],'classification':g0['classification'],'sft_action':g0['sft_action'],'primary_results_sha256':g0['primary_results_sha256'],'cases_executed':25,'primary_runs':1},'executorch':{'version':'1.5.0','exact_target_status':'BLOCKED','experiment_label':audit['experiment_label'],'torch_export':'PARTIAL_STATIC_PASS_DYNAMIC_FAIL','edge_lowering':'PASS_DIAGNOSTIC_ONLY','xnnpack':'PARTITIONING_PASS_RUNTIME_METHOD_LOAD_FAIL_DIAGNOSTIC_ONLY','custom_ops_required':None,'custom_or_decomposition_candidates':['aten::sort.values'],'blocking_ops':['aten::sort.values'],'decode':'NOT_EXPORTED','preliminary_classification':'BLOCKED'},'smollm2_fallback':{**phone,'cross_build':'PASS','generation_works':None,'model_loaded_offline':None},'kpack':{'build':True,'sign':True,'validate':True,'inspect':True,'desktop_identifier_query':True,'android_signature_verify':None,'android_query':None,'corruption_tests':True,'python_tests_passed':49,'jvm_tink_signature_verify':True,'android_instrumentation_status':'BLOCKED_PENDING_PHONE','calibration':'UNCALIBRATED_DEVELOPER_ONLY','archive_sha256':pack['archive_transport_sha256'],'manifest_sha256':pack['manifest_sha256'],'cached_input_rebuild_archive_identical':True},'android':android,'week2_ready':False,'blockers':blockers,'week2_recommendation':'Hold Week 2 until physical-phone product and KPack gates pass and the user reviews this evidence. G0_FAIL keeps MoR as a research/control model; DO NOT ESCALATE SFT. Prefer validated SmolLM2 for product continuity once phone evidence exists.'}
validity_note=''
diagnostic_path=ROOT/'gates/g0/diagnostics/inference_consistency.json'
if diagnostic_path.exists():
    diagnostic=json.loads(diagnostic_path.read_text(encoding='utf-8'))
    assert diagnostic['primary_results_sha256']==g0['primary_results_sha256']
    checks=diagnostic['results']
    divergent=[c['case_id'] for c in checks if not c['sdpa_first16_matches_eager']]
    summary['g0'].update(canonical_author_stack_equivalence='UNPROVEN',attention_backend_sensitivity_detected=bool(divergent),validity_review='gates/g0/diagnostics/inference_validity_review.md',inference_consistency=dict(sample_cases=len(checks),tokens_per_case=16,manual_matches_saved=sum(c['manual_repeat_matches_primary_first16'] for c in checks),manual_matches_hf_generate=sum(c.get('hf_generate_matches_manual',False) for c in checks),eager_matches_sdpa=sum(c['sdpa_first16_matches_eager'] for c in checks),divergent_cases=divergent))
    if divergent:summary['blockers'].append('Eager/SDPA continuation divergence detected: '+', '.join(divergent)+'. Canonical attention-stack validation is required before generalizing the eager-run G0 result.')
    validity_note='\n## Follow-up inference validity audit\n\nThe primary G0 scores describe the recorded eager configuration and remain unchanged. The diagnostic compares saved outputs, our loop, Hugging Face generation and SDPA on three 16-token continuations. Attention-backend equivalence and canonical author-stack replication remain **UNPROVEN**; broader conclusions about MoR are provisional. See [the validity review](../gates/g0/diagnostics/inference_validity_review.md) for measured agreements and divergence.\n'
write('artifacts/week1/week1_summary.json',summary)
report=f'''# PackRAG-MoR v1.2 — Week 1 Result

**Week 1 is incomplete. Week 2 readiness: BLOCKED.** The user reported the physical phone unavailable; ADB lists no device. No phone inference or Android instrumentation result is substituted with a desktop test or APK build.

## 1. Official MoR

- Checkpoint: authors' `250720_pretrain_smollm-360m_rec3_middle_cycle_random_lr3e-3_mor_expert_linear_alpha_0.1_sigmoid_aux_loss_0.001/pytorch_model.bin`, {mor['checkpoint_bytes']:,} bytes. Non-KV-sharing, rec3 expert-choice MoR; strict state dict: all keys matched.
- SHA-256: `{mor['checkpoint_sha256']}`.
- Repository commit: `{audit['mor_repository_commit']}` from the [authors' repository](https://github.com/raymin0223/mixture_of_recursions).
- Config hash: `{mor['config_sha256']}`. Tokenizer aggregate hash: `{mor['tokenizer_sha256']}`. Per-file hashes and resolved config: [reference metadata](../reference/mor/reference_metadata.json).
- Host: native Windows 11, RTX 4090 Laptop 16 GB; isolated Python 3.12.13 / PyTorch 2.6.0+cu124 / Transformers 4.52.4. Attention: explicitly selected eager, BF16 CUDA. Generation: `full_prefix_reference`, greedy, no cache.
- Status: **PASS** for loading and deterministic desktop generation. Three fixed prompts repeated with identical 16-token sequences; eager/SDPA selected-next-token checks agreed. FlashAttention equivalence was not established. [Golden reference](../export/golden_mor_reference.json).

## 2. Gate G0

| Category | Passed / total |
|---|---:|
| Direct | 5 / 10 |
| Citation | 0 / 5 |
| Abstention | 0 / 5 |
| Adversarial | 0 / 5 |

Classification: **G0_FAIL**. SFT action: **DO NOT ESCALATE**. The first and only primary run used all 25 frozen cases, exact prompt contract and fixed decoding, with no retrieval or prompt revision. Primary result SHA-256: `{g0['primary_results_sha256']}`.

Direct scoring credits supported requested facts despite malformed wrappers; citation, exact abstention and adversarial system-policy compliance are separate. All 25 outputs fail product syntax validation. Repeated wrapper/tag text dominates many outputs. This is measured failure of the pretrained checkpoint under the frozen evidence contract. No SFT was performed. [Adjudication and report](../gates/g0/g0_report.md).

## 3. ExecuTorch MoR Audit

Required target: ExecuTorch 1.5.0 with its source-pinned PyTorch. **Exact target BLOCKED:** required commit `{audit['pinned_pytorch_commit']}` differs from the wheel's `{audit['actual_pytorch_commit']}`. The wheel was not adopted as an architectural substitute. Every result below is `NON_PINNED_PYTORCH_DIAGNOSTIC`.

- E0 Add: export/edge/serialization and Windows execution passed.
- E1/E2: actual official checkpoint forward/static strict capture passed at batch 1, sequence 64, FP32 CPU, no cache.
- E3 bounded sequence 48–96: failed symbolic guards from `int(capacity_factor * seq_len)` at capacities 1, 2/3 and 1/3.
- E4 edge + portable serialization: passed; {audit['audit_steps']['E4']['value']['serialized_bytes']:,} bytes. This does not establish execution or numerical parity.
- E5 XNNPACK partitioning/serialization: passed. Initial missing `flatc.exe` tooling failure was repaired using the wheel's bundled executable.
- E6 Windows method loading: both portable and XNNPACK artifacts fail with missing `aten::sort.values` (three routing instructions).
- E7: v1.5 has an ATen sort entry, but no portable entry. A small portable sort kernel or equivalent routing decomposition is a candidate; exact pinned Android linkage remains untested. No custom kernels were built.
- E8: fixed prefill analyzed; explicit mutable cache/state decode remains **NOT_EXPORTED**. Per-family classifications, routing operations and delegated/remaining operators are in [the audit JSON](../export/mor_export_report.json).

Preliminary Android MoR classification: **BLOCKED**. This is not the Week 3 final viability decision. First blocker is the exporter pin mismatch; subsequent measured diagnostic blockers are routing shapes and sort registration. Golden-logit equivalence on the deployment runtime remains unproven.

## 4. SmolLM2 Product Fallback

- Physical target phone: **unavailable / not detected**.
- Official model: `HuggingFaceTB/SmolLM2-360M-Instruct`, revision `{conversion['model_revision']}`.
- GGUF: F16 correctness artifact, {conversion['gguf_bytes']:,} bytes, SHA-256 `{conversion['gguf_sha256']}`. Official 49,152-token vocabulary and chat template inspected. [Conversion metadata](../fallback/smollm2/conversion/conversion_metadata.json).
- llama.cpp candidate: `{conversion['llamacpp_candidate_commit']}`. Android arm64/API 28 CPU cross-build passed for `llama-cli` and `llama-completion`. The candidate is **not phone validated**; validated commit remains null. The source-supported batch harness uses `llama-completion` with the official rendered template.
- Offline model load/generation: **NOT RUN**. TTFT, load time, tokens/s, peak memory and five-case smoke score: **NOT MEASURED**.
- Status: **BLOCKED_PENDING_PHONE / WEEK1_PRODUCT_GATE_FAIL** (acceptance unmet because hardware is unavailable; no measured model failure is claimed).

Prepared smoke uses two direct, one citation, one abstention and one adversarial case from the same frozen G0 contract. Process success alone remains pending adjudication. [Phone report](../fallback/smollm2/phone_test_report.md).

## 5. Synthetic KPack

Build, sign, Python validate, inspect and identifier lookup: **PASS**. Ten fictional G0 chunks; real pinned Granite 384-dimensional CLS/L2-normalized float32 vectors; normative SQLite/FTS5 schema; KDX1 84-byte header; RFC 8785 manifest; raw Ed25519 signature verified before parsing authenticated metadata. The disposable writable DB copy is used for integrity/FTS checks; the original is unchanged and mounted read-only.

- Archive SHA-256: `{pack['archive_transport_sha256']}`.
- Manifest SHA-256: `{pack['manifest_sha256']}`.
- Aster-9 lookup returns chunk `69438bc99216b82f99d2df70`, containing the documented 74 °C fact. Identifier lookup requires subsequent evidence admission; hybrid retrieval is outside Week 1.
- Calibration: **UNCALIBRATED / developer-only**, allowed by architecture §12.3; ordinary release validation rejects it. No thresholds were guessed.
- Test key: `{vector['key_id']}`; **TEST KEY ONLY — NEVER USE FOR RELEASE**. Private fixture seed is intentionally public for reproducibility and is absent from both APKs.
- Python tests: **49 passed**, including frozen G0 integrity, output admission, signature failures, ZIP attacks, payload hash corruption, KDX corruption and re-signed malicious DB/schema/FTS fixtures.
- Android/JVM Tink vector and output validation: **2 tests passed**, including the five negative signature cases. Android app and instrumentation APKs: **BUILD PASS**, arm64 only, min 28 / target 37, no INTERNET permission.
- Actual Android signature verification and SQLite query: **BLOCKED_PENDING_PHONE**, not measured. [Verification results](../artifacts/week1/android/android_verification_results.json).
- Rebuilding from the same frozen inputs and cached Granite vectors produced byte-identical signed archives. No cross-platform embedding or ZIP-byte reproducibility claim is made.

## 6. Week-1 Overall

MoR research path: reference proven; pretrained gold-evidence behavior fails. Retain MoR as a research/control model and do not escalate SFT. Export diagnostics identify concrete routing/runtime work, but exact pin and Android numerical equivalence remain unresolved.

Product continuity path: official fallback converted and Android binaries/APKs compiled; on-device continuity remains unproven. **Week-2 readiness: BLOCKED.**

Blocking items:

{chr(10).join('- '+item for item in blockers)}

Recommended action: resume the physical-phone offline generation, five-case evidence smoke, measurements and KPack instrumentation when the device is available; review these results before beginning Week 2. Resolve the exact exporter pin before relying on MoR deployment diagnostics. Do not postpone the product gate while building large custom MoR operators. No Week 2 work was started.

## Deliverables and evidence

1. [This Week 1 report](week1_report.md)
2. [Machine-readable summary](../artifacts/week1/week1_summary.json)
3. [G0 report](../gates/g0/g0_report.md)
4. [All 25 primary raw outputs](../gates/g0/g0_results.jsonl)
5. [MoR export JSON](../export/mor_export_report.json)
6. [MoR export report](../export/mor_export_report.md)
7. [Phone report](../fallback/smollm2/phone_test_report.md)
8. [Phone results](../fallback/smollm2/phone_test_results.json)
9. [Signed synthetic KPack](../packs/synthetic-week1/org.packrag.synthetic.week1-1.0.0.kpack)
10. [Android verification results](../artifacts/week1/android/android_verification_results.json) and [APK artifacts](../artifacts/week1/android)
11. [Toolchain lock](../toolchain.lock.json)
12. Blocking items above
13. Recommended Week-2 action above

Baseline environment, hardware, dependency locks and artifact hashes are under `artifacts/week1/environment/`. Raw successful, failed and interrupted build/test logs are under `artifacts/week1/logs/`; [implementation notes](implementation_notes.md) explain the fixes. Local branch: `week1-v1.2-foundation`. No remote publish occurred.
'''
(ROOT/'docs/week1_report.md').write_text(report+validity_note,encoding='utf-8')
print('Saved Week 1 report, summary, provisional toolchain lock and blocked Android acceptance evidence.')
