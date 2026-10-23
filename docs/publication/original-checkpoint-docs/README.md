# PackRAG-MoR v1.2 — Week 1

Week 1 evidence and implementation spike. Read [docs/week1_report.md](docs/week1_report.md) and [artifacts/week1/week1_summary.json](artifacts/week1/week1_summary.json) for measured outcomes and unresolved gates. The authoritative source is [docs/architecture-v1.2.docx](docs/architecture-v1.2.docx).

The pretrained official expert-choice MoR is the primary G0 model. SmolLM2 is the product continuity candidate. No SFT, Week 2 retrieval, production registry, or final app is included.

## Local environments

Use Python 3.12 and separate virtual environments. `requirements-mor.txt` and `requirements-pack.txt` are direct dependencies; exact resolved versions live in `artifacts/week1/environment/requirements-*-resolved.txt`. Source commits, artifacts and unvalidated pins are recorded in `toolchain.lock.json`. Weights/toolchain downloads are ignored by Git and remain local.

Native Windows was used for every workstream. Android tools live under `vendor/`; build scripts set process-scoped paths and use project-local caches. No global toolchains were replaced.

## Reproduce completed checks

```powershell
& ./.venv-mor/Scripts/python.exe reference/mor/run_reference.py
# The primary G0 runner refuses to overwrite its frozen result.
& ./.venv-pack/Scripts/python.exe gates/g0/score_g0.py
& ./.venv-pack/Scripts/python.exe -m pytest tests -q
& ./.venv-pack/Scripts/python.exe -m kpack_builder.cli validate packs/synthetic-week1/org.packrag.synthetic.week1-1.0.0.kpack --public-key tests/signature_vector/public_key.raw --developer-mode
& ./.venv-pack/Scripts/python.exe -m kpack_builder.cli query packs/synthetic-week1/org.packrag.synthetic.week1-1.0.0.kpack Aster-9 --public-key tests/signature_vector/public_key.raw --developer-mode
& ./scripts/build_android.ps1
```

If recreating the toolchain, run `scripts/mirror_kotlin_compiler.py` first to populate the checked local compiler mirror.

The KPack is **UNCALIBRATED**, signed by a visibly marked, intentionally public **TEST KEY ONLY — NEVER USE FOR RELEASE** fixture. Release validation rejects it. Its 10 vectors are real Granite embeddings. Identifier lookup is a Week 1 evidence plumbing test, and does not grant answer permission.

## Export audit

`export/audit_mor.py` exports fixed prefill on the actual official checkpoint. It labels the installed wheel experiment `NON_PINNED_PYTORCH_DIAGNOSTIC`; it is not fulfillment of the exact pinned runtime contract. Set `FLATC_EXECUTABLE` to the isolated wheel's `executorch/data/bin/flatc.exe`. Run `export/analyze_runtime.py` after the export and runtime logs are available to add method-load and operator findings. Cache/decode and Android execution remain unproven.

## Resume the physical-phone gates

The user reported the target phone unavailable. Prepared instrumentation and generation harnesses require a USB-debuggable physical arm64 Android phone. They reject emulators and do not infer success from compilation.

```powershell
& ./fallback/smollm2/android/build_llama.ps1
# Inspect device readiness first; --run additionally requires offline settings.
& ./.venv-convert/Scripts/python.exe fallback/smollm2/android/phone_gate.py
& ./.venv-convert/Scripts/python.exe fallback/smollm2/android/phone_gate.py --run --serial DEVICE_SERIAL
```

Generation process success leaves the harness at `GENERATED_PENDING_ADJUDICATION`. Review the five raw cases and collect actual load time, TTFT, throughput and memory before setting a phone PASS or locking a validated llama.cpp commit. Run the Android `PackInteroperabilityTest` on that same physical phone, then pull its `android_verification_results.json`. The signed manifest and public key ship in the APK; the private fixture seed does not.

Week 2 must wait for the missing Week 1 acceptance evidence and user review.
