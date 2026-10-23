# ADR-001 — LFM2.5 product generator in v1.3

Status: ACCEPTED by the supplied v1.3 architecture, 4 October 2026 (§7.10 and Appendix H). Recorded in this repository on 5 October 2026. Earlier proposed ADR files retain their original statuses.

Decision: exact `LFM2.5-2.6B-QAD-Q4_0.gguf`, SHA256 `a247afd6414918eac8e520a9e6137dc271235461ecbe1180462221d5b8d40b03`, via llama.cpp commit `19e28a27702117d8f2eb16b825b9a308111f67d9`, is the product backend. Official MoR remains desktop research/control; SmolLM2 is historical.

Evidence: immutable candidate desktop and post-restart physical-phone runs each passed 25/25 frozen G0 cases with 25/25 semantic/scoring parity. Prior measurements and severe/critical stress thermal observations retain their original limits.

Migration: actual system/user roles through the official LFM template; reasoning/final separation; exact LFM tokenizer budgets 2048 context/1536 prefill/512 total new/4 evidence chunks/1200 evidence-token cap; clean generator-independent APIs and Android product module. KPack1.0/security/mobile-v1 retrieval remain unchanged.

Acceptance: rerun serialized-input/generator golden tests for runtime/model/template/compiler changes, and integrated product tests. Local/no-INTERNET app behavior, physical app integration and realistic-cadence thermal characterization are still required. No claim that the earlier shell experiment fulfilled the final Android application Definition of Done.

Rollback: preserve pinned validated artifacts; any later product substitution needs a new ADR and the same promotion/golden suite.
