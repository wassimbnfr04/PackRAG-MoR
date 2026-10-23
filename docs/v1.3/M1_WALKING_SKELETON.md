# M1 verified desktop walking skeleton — 5 October 2026

M1 is a real integrated development slice. It is not final v1.3 release acceptance. M0 and M1 pass; M2–M8 remain required.

## Inputs and identities

The source architecture is the immutable captured v1.3 DOCX, SHA256 `9b02f83b186a5b7f0101add861c6ecb40f5eb0b13016f50fa0c76efc6de07536`. `product/config/toolchain.lock.json` records exact model, tokenizer, official template, license, runtime binary and embedding profile hashes. Granite uses revision `c61e626a6255c490879d0af885078b61929d51f6`; its official FP32 ONNX SHA256 is `68e592b160673d30250824c1116bc6ab33f70efb22b97c9e1d7ce1e69c1c9d70`. The manually supplied LFM GGUF was hashed again; its bytes match v1.3. No LFM download, quantization, model adaptation or fine-tuning was performed.

The first ten immutable historical G0 direct facts were read as synthetic development source text. New source/chunk identities, v1.3-profile document inputs, actual ONNX document vectors, SQLite/FTS index, KDX and a new signed KPack were built under `artifacts/v1.3/m1/smoke-0001/developer-pack`. The historical facts, original vectors, packs, source manifests, answers and experimental reports were not modified. The new pack is UNCALIBRATED, with no fabricated numeric thresholds. Its private signing seed existed only in memory; its development public key is supplied explicitly for this test and is not a release trust anchor.

## What executed

The desktop implementation imports only the audited shared KPack data-format library from the old implementation. It does not import or execute historical model/phone experiment runners. New product modules implement the question path:

1. Copy the requested transport into a private snapshot. Verify raw-manifest Ed25519 signature before interpreting authenticated fields; validate canonical JSON, declared payload hashes/lengths, DB/FTS and KDX contracts. Match the entire signed embedding profile against the new exact product profile.
2. Open the verified DB read-only/immutable with trusted schema disabled. Read KDX through a read-only memory mapping. Activate this pack in a small session registry. Durable install/update/rollback is a later milestone.
3. Preserve the raw question and explicit `as_of`. Apply eligibility before retaining sparse/dense top-k. Query FTS5 BM25, compute actual normalized-query-vector dot products, perform local RRF and stable tier/order/cap handling, then merge/deduplicate candidates with recorded origins.
4. Resolve eligible exact aliases with word boundaries. This uncalibrated developer pack admits only eligible exact matches. It cannot admit a semantic-only question using invented release thresholds. An exact identifier permits consideration of its evidence, not an automatic answer.
5. Build the exact architecture system message and evidence records. Apply the hash-pinned official LFM template. Compare the server's template serialization to independent Jinja serialization, and verify explicit one-BOS tokenization equals tokenizer-added BOS tokenization.
6. Measure full prefill and evidence with the actual llama.cpp GGUF tokenizer. Enforce at most four chunks, evidence cap 1200, prefill cap 1536, context 2048 and generated cap 512. Recheck selected-evidence relevance/eligibility and frozen pack identities immediately before generation.
7. Generate through an owned, separately launched WSL CPU server at the exact llama.cpp commit. One server slot and a mutex serialize generation; decoding is greedy, temperature 0, top-p 1. The model remains loaded for the sequence. Complete output is buffered.
8. Require a completed reasoning delimiter and nonempty final text. Remove the reasoning before producing any public answer. Exact `INSUFFICIENT_EVIDENCE` becomes a dedicated abstention state. Reject unknown/malformed/missing citations and uncited paragraphs. Accepted source records contain canonical text, original locator, publisher and pack version.

Reserved model-control strings in ordinary input fields are explicitly rejected instead of silently editing canonical text or allowing template delimiters to enter data. More comprehensive adversarial coverage, translated evidence, conflict handling, cross-pack ambiguity, redundancy-aware selection, persistent lifecycle and cancellation remain M3/M4 work; this milestone does not claim they are finished.

## Validation and failures

M0 baseline: 49 historical tests passed in `m0/run-0003`; combined foundation gate: 53 passed in `m0/run-0004`. Earlier sandbox attempts encountered Windows temporary-directory permissions. Approved execution solved those environment failures without changing legacy implementation or experiment results.

M1 first gate: 73 passed, one failed because a new architecture-source test used the Windows default character encoding. The test was repaired to read UTF-8; progression was stopped until `m1/run-0002` passed all 74 tests. These include unit, signature/SQLite/KDX format, pack/retrieval adjacent integration, output/prompt contracts and all existing regressions. Synthetic unit encoders/token counters are clearly named fixtures; they are not used as evidence of real model integration.

The actual `m1/smoke-0001` run passed 14 cases: all ten direct supported questions produced structurally valid cited answers containing the frozen expected fact; no active pack returned a dedicated state without generation; an unrelated question failed the relevance gate; an exact model identifier with a purchase-price question generated deterministic insufficient evidence; and modified KDX bytes failed payload hash validation before activation. This is a bounded automatic smoke criterion, not a human judgment that every possible answer is semantically correct.

The independent `m1/parity-0001` run loaded the pinned source weights through official Transformers on CPU/FP32, took CLS and L2-normalized it, and compared four input forms to the product ONNX encoder. All passed the predeclared maximum absolute error `1e-4` and cosine `0.99999` criteria; observed maximum absolute error was `1.6391277313232422e-7`. This is numeric encoder parity, not the separate 24-question Darija/Arabizi/French/English retrieval acceptance probe.

Generator timings and emitted token counts come from llama.cpp. Reasoning/final partition uses actual emitted token IDs. Nonstreaming TTFT is explicitly null/unmeasured. Host generation wall time and total question time include host/API overhead; they are not Android latency or model-load timing. Server start-to-health is labelled separately. The server was stopped using its recorded PID only after matching its executable and dedicated port; shutdown returned success.

No raw hidden reasoning is persisted. New JSON records retain selected evidence IDs/hashes, full candidate ranks/scores, final accepted answers, citations, canonical sources, abstention/rejection states and token/timing metadata. Logs contain runtime operational timings, not completion reasoning text. Output-hash and source/result manifests support reproduction. Result manifests that are recorded after test execution explicitly distinguish recording-time source hashes from test-start identities.

## Reproduction and interpretation limits

From the repository root, use the existing pinned Python environment. Acquire Granite once with `python -m scripts.v13_acquire_granite`, freeze verified identities with `python -m scripts.v13_pin_assets`, and use a **new** output directory for every run:

```powershell
.venv-pack/Scripts/python.exe -m pytest tests product/tests -q -p no:cacheprovider --basetemp artifacts/v1.3/m1/NEW-RUN/pytest-temp --junitxml artifacts/v1.3/m1/NEW-RUN/combined-junit.xml
.venv-pack/Scripts/python.exe -m scripts.v13_smoke --run artifacts/v1.3/m1/NEW-SMOKE
.venv-pack/Scripts/python.exe -m scripts.v13_embedding_parity --run artifacts/v1.3/m1/NEW-PARITY
```

Create the pytest results parent first; Windows execution may need approved access for pytest's private temporary-directory ACLs. The smoke requires Kali WSL and refuses an occupied dedicated port. Exact model/template/runtime assets must exist at the recorded local paths. Weight distribution remains governed by the license and earlier owner preference to exclude large weights from packages.

M1 does not establish Android parity or performance, calibrated real-pack relevance, high-stakes translation review, two release demonstrators, PackBench statistics or final product acceptance. Those are explicit later gates in PLAN.md. No earlier MoR/SmolLM/LFM outcome has been reinterpreted or relabelled by this development smoke.
