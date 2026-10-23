# MoR ExecuTorch 1.5 audit

Target-pin status: **BLOCKED: PyTorch commit mismatch**.

Requested `41ffbc4a994e058af9fe00ed5caba73fc1033359`, installed `08187d9e0fba026dc8217405802ab5381dc88d90` (2.14.0+cpu). All wheel-based results are `NON_PINNED_PYTORCH_DIAGNOSTIC`. The official installer expects the source-pinned PyTorch to be installed first; no compiler/source-built PyTorch was present in the baseline. The wheel has not been adopted as an architectural substitute.

- E0: PASS
- E1: PASS
- E2: PASS
- E3: FAIL
- E4: PASS
- E5: PASS
- E6: PARTIAL (Windows method loading fails; Android untested)
- E7: ANALYZED (portable sort kernel or decomposition candidate)
- E8: ANALYZED_NOT_EXPORTED

Static capture first failure: `none`

Prefill tested on the actual loaded official checkpoint. Decode/cache state is not yet exported. Operator statuses remain UNKNOWN where Android kernel/linkage tests were not run. No custom operators were built.

Preliminary target classification: **BLOCKED**. This is not the Week 3 final viability decision.

## Post-export runtime audit

The diagnostic Add program executed correctly on Windows. Loading the serialized portable MoR method fails because `aten::sort.values` is not registered (three routing instructions reference that operator). The v1.5 source has an ATen entry, but no portable functions.yaml entry. This identifies a small custom portable kernel or graph decomposition candidate; no kernel was implemented and no Android linkage was tested. XNNPACK method-load outcome: FAIL.

The bounded dynamic capture failure comes from symbolic `int(capacity_factor * seq_len)` routing guards at capacities 1, 2/3 and 1/3. Fixed prefill is captured at batch 1, sequence 64. Explicit cache/state decode is not exported.

The JSON includes per-family classifications and the exact delegated/remaining operator lists. “Serialized” does not mean linked, executed, numerically equivalent, or phone validated.
