# G0 inference validity review

This review answers the user's question about test correctness. It is **NOT_PRIMARY_G0**. The primary outputs, scores, prompts and hashes remain unchanged.

The official source checkout has no local modifications. The primary model uses the official expert-choice experiment's config, checkpoint and tokenizer, the official sharing transformation, strict state-dict loading, evaluation mode, BF16 CUDA and explicitly selected eager attention. The frozen prompt matches the user's exact contract. All 25 saved inputs contain 215–261 tokens, so no input was truncated. Each case used greedy decoding and the required 128-token maximum. Input/output hash checks pass.

Additional runtime checks used G0-D01, G0-D02 and G0-A01 with their original prompts. For all three, the first 16 tokens:

- reproduce the saved primary output;
- match Hugging Face `generate()` on the loaded official model, with greedy decoding and cache disabled;

Eager and SDPA continuations agree on G0-D01 and G0-D02. They **diverge on G0-A01 at the second generated token**: eager begins repetitive METHOD tags, while SDPA starts a source-tag/evidence continuation. This was not visible in the earlier three-next-token preflight. The SDPA output is only a 16-token diagnostic; it was not scored as a replacement G0 run.

See `inference_consistency.json` and `artifacts/week1/logs/g0_inference_consistency_audit.log`. These checks support the correctness of the generation harness for the tested eager settings, but **do not establish attention-backend equivalence**. The observed divergence requires further reference validation before presenting G0 as a canonical author-stack replication. This review does not identify the cause of the divergence; numerical sensitivity or implementation differences require separate investigation.

Limitations:

- No author-stack FlashAttention comparison was performed. The original eager/SDPA check covered three next-token predictions and had maximum absolute logit differences of 0.15625; agreement in selected tokens does not imply identical logits. This additional check covers only three 16-token continuations.
- Cached autoregressive inference was not compared with the full-prefix reference.
- Semantic scoring was adjudicated by Codex and has not received an independent human review. Raw outputs and per-case rationales are available for that review.
- G0 evaluates one pretrained checkpoint under one frozen evidence/instruction contract. It is not an evaluation of every MoR checkpoint, general language-model quality, the architecture's research claims, or an adapted model.
- The ExecuTorch pin mismatch affects the separate deployment audit, not the primary PyTorch 2.6 G0 environment. Android deployment remains unproven.

The supported conclusion is **G0_FAIL for this pretrained checkpoint in the recorded eager reference configuration**, with canonical author-stack equivalence **UNPROVEN**. The recorded scores remain valid descriptions of that run; the broader model conclusion is provisional. The evidence does not support the statement “MoR completely failed.” Failure is not purely a citation issue: saved outputs also change a documented blue flash to red and invent an unknown Motor M2 speed. Conversely, direct scoring credited five supported facts despite malformed output, and G0-X05 resisted the injected instruction and gave the correct location but failed the citation policy.
