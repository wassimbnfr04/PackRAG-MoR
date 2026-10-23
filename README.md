# PackRAG-MoR

A small on-device language model supported by signed, replaceable knowledge
packs. PackRAG retrieves applicable evidence outside the model weights, then
generates a source-bound answer locally.

**Published baseline: the full project implementation through M4 (M0–M4).**
This is the cumulative project, not an export of only the M4 changes. It starts from
the verified M4 checkpoint `8f0ccaa5cfac125c2ec2adf291cef3d1d7d4c3b0`.
M5–M8, final owner knowledge packs and final release acceptance remain unfinished.
Future work will be published incrementally.

## Implemented through M4

- Android chat application, pack management, local asset import and verification,
  source viewing and runtime diagnostics.
- Signed KPack verification, controlled activation, rollback/removal and registry
  persistence.
- Granite ONNX embeddings, identifier lookup, SQLite FTS5, dense retrieval,
  deterministic rank fusion, evidence admission and token-budget selection.
- Local LFM2.5 generation through llama.cpp; buffered reasoning removal and
  citation/output validation.
- Shared Python reference runtime, format/schema tooling, fixtures and regression
  tests, with recorded Android/physical-device validation.

The M4 app is an **evidence-only assistant**: without an active verified pack it
abstains. Its primary generation profile emits validated quotations from selected
sources. General chat without a pack, broader free-form synthesis and removal of
global legal query controls are future revisions, not features claimed here.

## Repository map

| Path | Purpose |
|---|---|
| [`product/android`](product/android) | Current Kotlin Android app and runtime modules |
| [`product/packrag`](product/packrag) | Current Python RAG implementation |
| [`product/tests`](product/tests), [`tests`](tests) | Product and shared regression tests |
| [`kpack_builder`](kpack_builder) | Shared pack format, schema and validation tooling |
| [`product/config`](product/config) | Asset/runtime pins and approved public publisher configuration |
| [`scripts`](scripts) | Build, fixture, smoke and evidence utilities |
| [`docs/adr`](docs/adr), [`docs/v1.3`](docs/v1.3) | Design decisions, implementation journey and acceptance records |
| [`artifacts`](artifacts) | Retained small test fixtures, manifests, logs and original evidence |

Root `android`, `desktop`, `reference`, `fallback`, `gates` and `export` preserve
earlier milestone code/evidence used by shared regression and historical records.
The current app is **`product/android`**, not the earlier Android spike.
Retained `artifacts/.../build-*` directories hold whitelisted textual test/build
records, not installed SDKs or compiled application builds.

All **176 Kotlin files and three Java test helpers** from the accepted Android
build inputs are included. External model weights, toolchains/caches, actual
private signing custody, compiled APK/JAR files and later host experiments are
excluded. The public interoperability seed under `tests/signature_vector` is an
explicitly documented **TEST KEY ONLY** fixture, never a release publisher key.

## Model and platform

| Component | Baseline |
|---|---|
| Generator | Liquid AI LFM2.5-2.6B, QAD-Q4_0 GGUF |
| Embedder | IBM Granite embedding 97m multilingual r2, ONNX CPU, 384 dimensions |
| Android | API28 minimum, ARM64; debug-only x86-64 native emulator option |
| Current app policy | Quoted-source profile, context3072/output1536 ceilings |
| Connectivity | App INTERNET permission removed; model and pack files are local |

The Python typed API retains its earlier baseline policy unless `QUOTES` is
explicitly selected. The app explicitly selects `QUOTES`. Exact asset hashes,
model revision, native commit and Android tool versions are in
[`product/config/toolchain.lock.json`](product/config/toolchain.lock.json).

## Setup and running

Start with [`docs/GETTING_STARTED_M4.md`](docs/GETTING_STARTED_M4.md), then the
existing [product run notes](product/README.md) and
[M4 reproduction/acceptance record](docs/v1.3/M4_REPRODUCTION_AND_ACCEPTANCE.md).

The repository is a source/evidence baseline, not a self-contained installer.
Restore the pinned model assets and external toolchains separately. Android
native builds require an exact clean upstream llama.cpp checkout at
`vendor/llama.cpp`; it is a separately pinned dependency, not omitted first-party
implementation. Publisher-private seeds are not required to run an already
approved signed test pack.

## Validation and limits

The historical M4 acceptance records report:

- 1,054 Python tests with zero failures/errors/skips.
- 99 Kotlin host test methods in the matched Android builds.
- Physical ARM native execution and the primary chat/source/diagnostic UI gate.
- Integrity checks on accepted sources and immutable experimental evidence.

Read [the M4 gate matrix](docs/v1.3/M4_FINAL_GATE_MATRIX.md) and
[publication verification](docs/publication/README.md) for scope and identities.
This publication does not relabel old tests as new tests. Any fresh publication
regression result is recorded separately in `docs/publication`.

These are development acceptance results, not held-out expert accuracy or a
controlled performance benchmark. One G0 citation case remains a counted failure
in the historical24/25 result. A complete phone repair guide was slow in the
recorded functional test; emulator observer timeouts remain failures. Final
release/resource/thermal acceptance and independent real-manual evaluation remain
future work. Source text and syntactically valid citations do not alone establish
that a procedure is complete or safe in the real world.

## Continuing development

Keep the integrated path working while adding independently verifiable changes:

`question → verified active pack → retrieval → admission → selection → generation
→ reasoning removal → output validation → accepted answer or abstention`

Use new output directories for new experiments. Preserve original evidence and
document known failures. [`PLAN.md`](PLAN.md), [`STATUS.md`](STATUS.md) and
[`DECISIONS.md`](DECISIONS.md) retain the milestone history; the publication status
is explained in `docs/publication`.

## Licensing

No first-party open-source license is assigned by this publication. The owner can
choose one separately; do not assume MIT or Apache licensing. External models and
dependencies retain their own licenses. See
[`docs/THIRD_PARTY_AND_MODEL_NOTES.md`](docs/THIRD_PARTY_AND_MODEL_NOTES.md).
