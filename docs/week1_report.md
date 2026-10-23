# PackRAG-MoR v1.2 — Week 1 Result

**Week 1 is incomplete. Week 2 readiness: BLOCKED.** The user reported the physical phone unavailable; ADB lists no device. No phone inference or Android instrumentation result is substituted with a desktop test or APK build.

## 1. Official MoR

- Checkpoint: authors' `250720_pretrain_smollm-360m_rec3_middle_cycle_random_lr3e-3_mor_expert_linear_alpha_0.1_sigmoid_aux_loss_0.001/pytorch_model.bin`, 330,419,534 bytes. Non-KV-sharing, rec3 expert-choice MoR; strict state dict: all keys matched.
- SHA-256: `471986c279ea75dbdd0034d4b10f1ee75652a94fe202327c5b437b362c02fc4c`.
- Repository commit: `82c97f29cd140efa01f5cc4fe0de73a4c3b6ffd6` from the [authors' repository](https://github.com/raymin0223/mixture_of_recursions).
- Config hash: `8e5f14f99693d2ad597509d23316eef20a96d88ca0cc9d97f55fb29747331591`. Tokenizer aggregate hash: `5b828199aaa40d7e4aa339aef7a8ce83b5913852b48b2f91e48248dce6869e63`. Per-file hashes and resolved config: [reference metadata](../reference/mor/reference_metadata.json).
- Host: native Windows 11, RTX 4090 Laptop 16 GB; isolated Python 3.12.13 / PyTorch 2.6.0+cu124 / Transformers 4.52.4. Attention: explicitly selected eager, BF16 CUDA. Generation: `full_prefix_reference`, greedy, no cache.
- Status: **PASS** for loading and deterministic desktop generation. Three fixed prompts repeated with identical 16-token sequences; eager/SDPA selected-next-token checks agreed. FlashAttention equivalence was not established. [Golden reference](../export/golden_mor_reference.json).

## 2. Gate G0

| Category | Passed / total |
|---|---:|
| Direct | 5 / 10 |
| Citation | 0 / 5 |
| Abstention | 0 / 5 |
| Adversarial | 0 / 5 |

Classification: **G0_FAIL**. SFT action: **DO NOT ESCALATE**. The first and only primary run used all 25 frozen cases, exact prompt contract and fixed decoding, with no retrieval or prompt revision. Primary result SHA-256: `98f7d75bd05ac4a470ef396cb8c8e98e4510ba44604339a79b97ced96db189e7`.

Direct scoring credits supported requested facts despite malformed wrappers; citation, exact abstention and adversarial system-policy compliance are separate. All 25 outputs fail product syntax validation. Repeated wrapper/tag text dominates many outputs. This is measured failure of the pretrained checkpoint under the frozen evidence contract. No SFT was performed. [Adjudication and report](../gates/g0/g0_report.md).

## 3. ExecuTorch MoR Audit

Required target: ExecuTorch 1.5.0 with its source-pinned PyTorch. **Exact target BLOCKED:** required commit `41ffbc4a994e058af9fe00ed5caba73fc1033359` differs from the wheel's `08187d9e0fba026dc8217405802ab5381dc88d90`. The wheel was not adopted as an architectural substitute. Every result below is `NON_PINNED_PYTORCH_DIAGNOSTIC`.

- E0 Add: export/edge/serialization and Windows execution passed.
- E1/E2: actual official checkpoint forward/static strict capture passed at batch 1, sequence 64, FP32 CPU, no cache.
- E3 bounded sequence 48–96: failed symbolic guards from `int(capacity_factor * seq_len)` at capacities 1, 2/3 and 1/3.
- E4 edge + portable serialization: passed; 661,232,692 bytes. This does not establish execution or numerical parity.
- E5 XNNPACK partitioning/serialization: passed. Initial missing `flatc.exe` tooling failure was repaired using the wheel's bundled executable.
- E6 Windows method loading: both portable and XNNPACK artifacts fail with missing `aten::sort.values` (three routing instructions).
- E7: v1.5 has an ATen sort entry, but no portable entry. A small portable sort kernel or equivalent routing decomposition is a candidate; exact pinned Android linkage remains untested. No custom kernels were built.
- E8: fixed prefill analyzed; explicit mutable cache/state decode remains **NOT_EXPORTED**. Per-family classifications, routing operations and delegated/remaining operators are in [the audit JSON](../export/mor_export_report.json).

Preliminary Android MoR classification: **BLOCKED**. This is not the Week 3 final viability decision. First blocker is the exporter pin mismatch; subsequent measured diagnostic blockers are routing shapes and sort registration. Golden-logit equivalence on the deployment runtime remains unproven.

## 4. SmolLM2 Product Fallback

- Physical target phone: **unavailable / not detected**.
- Official model: `HuggingFaceTB/SmolLM2-360M-Instruct`, revision `a10cc1512eabd3dde888204e902eca88bddb4951`.
- GGUF: F16 correctness artifact, 725,553,600 bytes, SHA-256 `4723b60dcc23b06f59c356e979c26e9f417195056eb60ecbbb6d95f78eb8cdd7`. Official 49,152-token vocabulary and chat template inspected. [Conversion metadata](../fallback/smollm2/conversion/conversion_metadata.json).
- llama.cpp candidate: `19e28a27702117d8f2eb16b825b9a308111f67d9`. Android arm64/API 28 CPU cross-build passed for `llama-cli` and `llama-completion`. The candidate is **not phone validated**; validated commit remains null. The source-supported batch harness uses `llama-completion` with the official rendered template.
- Offline model load/generation: **NOT RUN**. TTFT, load time, tokens/s, peak memory and five-case smoke score: **NOT MEASURED**.
- Status: **BLOCKED_PENDING_PHONE / WEEK1_PRODUCT_GATE_FAIL** (acceptance unmet because hardware is unavailable; no measured model failure is claimed).

Prepared smoke uses two direct, one citation, one abstention and one adversarial case from the same frozen G0 contract. Process success alone remains pending adjudication. [Phone report](../fallback/smollm2/phone_test_report.md).

## 5. Synthetic KPack

Build, sign, Python validate, inspect and identifier lookup: **PASS**. Ten fictional G0 chunks; real pinned Granite 384-dimensional CLS/L2-normalized float32 vectors; normative SQLite/FTS5 schema; KDX1 84-byte header; RFC 8785 manifest; raw Ed25519 signature verified before parsing authenticated metadata. The disposable writable DB copy is used for integrity/FTS checks; the original is unchanged and mounted read-only.

- Archive SHA-256: `2aa3a6283acecfd7927d7c28f229d8766e799e071e418f430ef3bbe8068bc5fc`.
- Manifest SHA-256: `4a5c81b87449e007674c88fa5b9e0fe6b5a6fbed1c23e03158b12c2fc4251216`.
- Aster-9 lookup returns chunk `69438bc99216b82f99d2df70`, containing the documented 74 °C fact. Identifier lookup requires subsequent evidence admission; hybrid retrieval is outside Week 1.
- Calibration: **UNCALIBRATED / developer-only**, allowed by architecture §12.3; ordinary release validation rejects it. No thresholds were guessed.
- Test key: `ed25519:67744919eb4747a5d16407c10e90287307a375fd6d5df28e4accbe2c7ee0b3e1`; **TEST KEY ONLY — NEVER USE FOR RELEASE**. Private fixture seed is intentionally public for reproducibility and is absent from both APKs.
- Python tests: **49 passed**, including frozen G0 integrity, output admission, signature failures, ZIP attacks, payload hash corruption, KDX corruption and re-signed malicious DB/schema/FTS fixtures.
- Android/JVM Tink vector and output validation: **2 tests passed**, including the five negative signature cases. Android app and instrumentation APKs: **BUILD PASS**, arm64 only, min 28 / target 37, no INTERNET permission.
- Actual Android signature verification and SQLite query: **BLOCKED_PENDING_PHONE**, not measured. [Verification results](../artifacts/week1/android/android_verification_results.json).
- Rebuilding from the same frozen inputs and cached Granite vectors produced byte-identical signed archives. No cross-platform embedding or ZIP-byte reproducibility claim is made.

## 6. Week-1 Overall

MoR research path: reference proven; pretrained gold-evidence behavior fails. Retain MoR as a research/control model and do not escalate SFT. Export diagnostics identify concrete routing/runtime work, but exact pin and Android numerical equivalence remain unresolved.

Product continuity path: official fallback converted and Android binaries/APKs compiled; on-device continuity remains unproven. **Week-2 readiness: BLOCKED.**

Blocking items:

- Target physical phone unavailable: offline SmolLM2 generation, five-case evidence smoke, performance/memory and Android KPack instrumentation are unrun.
- Exact ExecuTorch PyTorch source pin is unmet; current export/runtime artifacts are NON_PINNED_PYTORCH_DIAGNOSTIC only.
- Diagnostic MoR runtime cannot load aten::sort.values; dynamic routing shape guards fail; explicit cache/decode export and Android numerical parity remain unproven.

Recommended action: resume the physical-phone offline generation, five-case evidence smoke, measurements and KPack instrumentation when the device is available; review these results before beginning Week 2. Resolve the exact exporter pin before relying on MoR deployment diagnostics. Do not postpone the product gate while building large custom MoR operators. No Week 2 work was started.

## Deliverables and evidence

Follow-up test-validity audit: our full-prefix loop reproduces saved first-16-token outputs and matches Hugging Face `generate()` on three frozen prompts. Eager/SDPA continuations match on two, but diverge on G0-A01. Therefore attention-backend equivalence and canonical author-stack replication remain **UNPROVEN**. The primary G0 scores and hash remain unchanged; they describe the recorded eager configuration, and a broader conclusion about the checkpoint is provisional. [Validity review](../gates/g0/diagnostics/inference_validity_review.md).

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
