# Third-party and model notes

This repository contains first-party implementation, documented development test
material and retained evidence. Publishing it does not assign a new first-party
open-source license; that is a separate owner decision. External dependencies and
models remain governed by their own terms.

- Generator: `LiquidAI/LFM2.5-2.6B-GGUF`, exact QAD-Q4_0 artifact and official
  template identities in `product/config/toolchain.lock.json`. The recorded model
  license is `lfm1.0`, and public weight redistribution is not attested. Model
  weights are excluded.
- Embedder: `ibm-granite/granite-embedding-97m-multilingual-r2`, pinned revision,
  tokenizer and ONNX hashes in that same lock. Weight files are excluded.
- Native runtime: upstream `ggml-org/llama.cpp`, exact pinned commit in the lock;
  restore upstream source and its own LICENSE when building. It is not copied
  into this first-party source snapshot.
- Android/JVM/Python dependencies: versions are recorded in Gradle files and
  requirements/configuration. Their licenses are not replaced by this document.
- Manufacturer-derived development test digests carry source/provenance metadata
  in their fixtures and evidence. They are not an attestation of permission to
  redistribute complete original manuals or the owner's final knowledge packs.
- `tests/signature_vector/test_private_key` is an intentionally public,
  non-secret test seed. Its README explicitly forbids release use. Actual project
  publisher-private custody, signing keystores and credentials are excluded.

No claim of complete legal/license clearance or model redistribution rights is
made by a source cleanliness/hash check. Preserve original third-party notices
when restoring or redistributing dependencies under their applicable terms.
