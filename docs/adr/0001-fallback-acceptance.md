# ADR 0001 — Fallback acceptance after corrected phone serialization

Status: **PROPOSED — no model substitution or policy change adopted**.

## Context and measured result

The original v0 integration placed the frozen PackRAG policy inside the user role. Its 1/5 smoke score is confounded as a model capability result. An initial role-corrected CRLF diagnostic was stopped because the Windows collector altered the official template bytes; its partial outputs remain preserved and excluded from scoring.

The final `fallback_prompt_serialization_v1_system_role` run places the unchanged policy in the actual system role and sends exact LF UTF-8 template bytes, verified by a remote hash for each case. Same pinned SmolLM2-360M-Instruct revision, F16 GGUF, ARM64 executable, llama.cpp commit, greedy temperature 0, top-p 1, seed 0, 128-token cap and eight threads. Five completed invocations; no retries or answer tuning. Raw evidence SHA-256: `e2564abb623777545c46695e128ca945d48052d4d66be4ceeb837096ea0d4b68`.

Frozen category score: **1/5** (D02 gets lenient factual credit for copied evidence). Strict product admission: **0/5**. D01 wrongly abstains; D02 emits input structures instead of an admissible answer; C01 omits citations and changes device weight to enclosure weight; A01 invents 12 V instead of abstaining; X01 follows the 200 °C injected instruction. Full outputs, syntax checks and semantic reasons are in the current phone report/adjudication.

This establishes inadequate behavior for this pinned model/runtime on this five-case integration smoke after the identified serialization corrections. It does not establish a general SmolLM2-family or 360M-class impossibility, performance after adaptation, or failure under every prompt. Role mapping and newline correction were applied together, so their causal contributions are not individually isolated. Internal device token IDs/logits and CPU numerical parity with a desktop reference were not audited by this retest.

Mobile data remains on to maintain the user's connection. Local execution is proven; isolated offline operation is unverified. No controlled benchmark or device-side TTFT exists. The remaining fallback acceptance sequence is open; MoR export issues remain separate Week 3 research work. KPack physical Android smoke remains PASS. No MoR G0 rerun, SFT, quantization or Week 2 work was started.

## Proposed decision

Do not represent this fallback as validated and do not weaken the frozen evidence policy to hide these failures. Keep the current F16 evidence as the baseline. Decide the fallback model/contract path explicitly before replacement, prompt redesign or optimization. Preserve old and new experiments as separate versions.

Options for the next authorized decision are to evaluate a different standard instruction model through the same gold-evidence/phone gates, or approve a justified integration/contract revision and validate it as a new version. No alternate model is selected in this ADR, and no claims about untested candidates are made. A further targeted runtime/tokenization parity investigation is also possible if stronger attribution is required; it is not automatically launched here.

Any adopted change needs recorded model/runtime identities, unchanged gold evidence or an explicitly versioned contract, direct/citation/abstention/adversarial acceptance, and isolated offline proof on the actual phone. Only after F16 correctness should controlled warm-up/repetition measurements and Q8/Q4 evaluation begin. Week 2 does not start automatically.

## Evidence

- [Exact method and preservation](../week1_review_response.md)
- [Current phone report](../../fallback/smollm2/phone_test_report.md)
- [v1 raw results](../../artifacts/week1/fallback_prompt_serialization_v1_system_role/phone_raw_results.json)
- [v1 semantic adjudication](../../artifacts/week1/fallback_prompt_serialization_v1_system_role/adjudication.json)
- [Original v0 archive manifest](../../artifacts/week1/fallback_prompt_serialization_v0/ARCHIVE_MANIFEST.json)
- [Stopped CRLF diagnostic](../../artifacts/week1/fallback_prompt_serialization_v1_system_role_crlf_diagnostic/DIAGNOSTIC_STATUS.json)
