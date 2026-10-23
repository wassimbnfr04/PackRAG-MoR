# C2b conflict implementation and acceptance

Status: BOUNDED C2b VERIFIED on9 October after pending restoration and full acceptance preflight. Initial implementation followed C2a checkpoint3e765ae; pause checkpointe4469ef preserved completed gates. Later evidence/UI/release-pack/benchmark/product work remains incomplete. Earlier partial/failure paragraphs below are chronological, not the current acceptance state.

Full run0006 passes689 tests40.17s and587 unchanged historical identities.
Debug build0011 succeeds. Actual conflict-smoke0001 passes19 complete-tokenizer
scenarios and six of seven runtime assertions, then fails EXCEPTION's final
expected-answer assertion. The first harness did not save that failed final
validated result before asserting; its failed state/text cannot be inferred
from the combined assertion. DIAGNOSTIC_LIMITATION.json records this gap.
Server cleanup is retained. Phone execution and later milestones are held.
The runner now saves every final validated observation before assertion;
fresh0002 repeats the unchanged model/corpus/prompt/decoding/output policy for
diagnosis. No fixture gold or acceptance criterion has been rewritten.

Diagnosis0001 captures only completed final text, separately labeled as a
diagnostic candidate rather than a product answer; hidden reasoning is not
saved. The candidate correctly says74°C but references Source S2 in prose,
with no bracketed citation. Runtime correctly suppresses it as OUTPUT_REJECTED,
missing_or_unknown_citation. Both base/exception chunks are selected;277 prefill/
123 evidence/392 emitted tokens are below caps. This is a citation compliance
failure, not missing evidence or token exhaustion. Neither entire model failure
nor a causal hardware/software bottleneck follows from it.

Source paragraph548 specifies an XML QUESTION/CONTEXT/VERIFIED_EVIDENCE/SOURCE
envelope. The walking baseline used plain labels. C2b brings this already
required serialization forward from D to repair the integration, retaining the
exact system policy, official template, model/native/decoding and strict output
validation. XML-reserved data/attributes are escaped losslessly; canonical text
and raw query remain original in provenance. xml-prompt-unit0001 passes54
focused/admission/strict-output tests. Same frozen exception evidence under XML
in diagnostic0002 accepts74°C[S2]; the supported-answer criterion is unchanged.
This one-case repair observation is not complete acceptance.

xml-prompt-fixtures0001 freezes10 new actual GGUF full-template references,
preserving the old reference/pack/public-key bytes. New references use actual
normalized-query vectors, consistent with the product since B2. The retained
older tokenizer-only fixture used raw vectors; its former token/candidate order
is not relabeled as execution of the new format. New Android prompt parity uses
the versioned XML references; independent old retrieval/embedding evidence stays
unchanged. Fresh complete regression/build/desktop/phone gates are required;
build0011 and run0006 describe the pre-XML inputs, not the repaired final build.

The pure shared contract has40 independently specified expected decisions.
It covers ordinal0/max/null/equal values, curator/jurisdiction/provision scope,
equivalent text, multiple paragraphs of one original edition, inconsistent
edition ranks, full/partial publisher assertions, supersession/amendment/
exception direction, chains/cycles/self-cycles, absent endpoints, ignored cites,
caller-order reversal and unrelated alias targets. Initial Python contract
passes40 in conflict-unit0001; retained adjacent gate0001 passes157 and new
signed adjacent gate0002 passes188. These are not complete C2b acceptance.

Both runtimes now resolve already eligible retrieval hits before local/global
caps. The normal priority/RRF/exact/cosine/pack/chunk key still establishes
general relevance order. Authority changes only related-set members in their
occupied positions, preserves numeric sparse/dense ranks/RRF/cosine, and never
injects a relation endpoint. All eligible exact interpretations participate
before caps; they can clear ambiguity only inside one resolved set. Unknown,
incomparable, weakly asserted, inconsistent or cyclic sets remain explicit.
Several paragraphs of one source edition do not become competing versions.
Preferred-edition paragraphs survive together; amendment/exception companions
retain their base. Result/source conflict metadata records interpretation, while
existing SourceMetadata retains the original authenticated publisher claims.

Final prompt admission checks selected canonical original/text hash pairs.
An unresolved selected set yields LEGAL_CONFLICT_UNRESOLVED. Dropped required
companions yield INCOMPLETE_LEGAL_CONFLICT_EVIDENCE before generation. This is
an integrated fail-closed correctness baseline; D will improve coverage-aware
selection and the after-merge nonidentifier relevance gate. No global latest
document heuristic, graph expansion, acceleration or native/model/template/
decoding change is introduced. Arbitrary natural-language contradiction
detection or legal truth is not claimed.

conflict-fixtures0001 freezes19 new signed synthetic packs/19 retrieval
scenarios. Two ephemeral signers are never persisted. Exact source specs and
document embedding inputs are saved/hash-bound. Pinned Granite is actually run;
vectors are reused only for exact identical input strings. The explicit recipe
uses nonempty article else section/locator, empty contextual prefix and unchanged
canonical text. Independently fixed retained sets/ambiguity precede retrieval;
numeric candidate order/ranks/scores/conflict serialization are desktop parity
references, not independent legal gold. The before-cap case proves a LOST
interpretation is absent from the final16 while ambiguity remains. Five linked
companions cannot fit four chunks and must reject generation. Synthetic
UNCALIBRATED evidence is not a release pack or human source review.

Required acceptance before progressing to D:

- Full Python regressions, unchanged587 historical identities and prior B2/C1/
  C2a saved-output hashes; shared host contract on both Android build variants.
- New physical40-case/19-signed-scenario parity with actual Granite<=1e-4,
  exact ranks/RRF/origins/decisions, actual GGUF companion admission, and exact
  full-template tokenizer comparison with desktop19 scenarios.
- Real desktop/phone authority/supersession/exception74°C answers with retained
  canonical metadata, plus zero-generation unknown/incomparable/before-cap and
  five-companion rejections. Controlled Python generation is protocol-only.
- Retained14 real desktop cases and all development/policy phone security,
  interval, identifier, Unicode, prompt, cancellation/recovery and lifecycle
  gates. Save every final JSON before changing variants; restore development
  with consent checks. Bind source, APK, corpus, native and result identities.

Mobile data remains ON; the app has no INTERNET permission. Explicit isolated
developer-trust fixtures test the core on both variants, not production default
admission. Compiled default production policy has its separate retained gate.
Instrumentable demo is Debug signed, not the final nondebuggable release.
Functional run timings do not establish peak memory, release performance or a
causal hardware/software bottleneck. Owner models and registries are preserved.

Final-source observation (not closure): run0007 passes691 regressions/587 historical identities; builds0012/0013 each26 host methods/458 equal inputs. Retained desktop smoke0006 passes14 cases, conflict-smoke0003 passes19 token scenarios and7 actual runtime cases. Phone first two methods pass40/19 and7 cases respectively, including allthree supported74°C cited answers. The complete22-method development gate,17-method policy gate, result collection/restoration/closure remain required. Runtime inputs143 are unchanged. Demo inspection0007 is instrumentable/non-final. The closure adapter preparation assertion is preserved in conflict-gate0001/PREPARATION_FAILURE.json; it occurred before any closure output, not in product execution.

C2b development gate observation: all22 phone methods pass1188.247s; all22 final structured JSON results are saved before installing demo0013. Exact19 tokenizer/admission comparisons and7 runtime states/selected supported-case token counts match desktop. Original ADB bytes for observed and collected results are preserved; primary runner formatting is identified. The17-method production-policy gate is running; restoration/closure remain pending, so C2b is not yet verified. Instrumentation duration uses a locale thousands separator (U+202F); the closure parser removes numeric whitespace before comma-decimal conversion and confirms1188.247, rather than truncating the duration.


Owner pause instruction (7 October): finish only the already-running17-method production-policy gate, save every output and stop. No debug restoration or new test begins after that gate. Restoration0007 and full C2b acceptance remain pending until explicit owner continuation with the phone available. The instrumentable demo build0013 remains installed; owner assets/registries are preserved. A public work-in-progress pause checkpoint records completed gates without declaring C2b verified.

Final connected-gate observation before owner pause: development22 methods pass1188.247s; production-policy17 methods pass757.06s. All39 final JSON outputs saved before stopping. Both variants pass shared40/signed19/actual tokenizer19/runtime7/XML prompt10 and retained adjacent/security gates. Restoration0007 is deliberately NOT run, demo0013 remains installed, and C2b closure is NOT written. conflict-pause0001 checks completed gates/source/APK/corpus/history identities and saves a public work-in-progress checkpoint. Next explicit resume requires debug restoration/consent, then full acceptance closure before D.

Resumption9 October: phone authorized;143 runtime/458 Android inputs, saved pause outputs and debug0012 APKs match before installation. Unchanged development restoration0007 passes one method/four consent checks6.062s. Full closure preflight verifies every prerequisite, official corpus/APK/native/source/fixture/token IDs/selected runtime evidence and587 historical identities. The22/17 phone gates and691 regressions are retained7 October executions, not new9 October performance tests. Mobile data remains on. No native/model/template/decoding change occurs. C2b is accepted within the declared synthetic protocol/functional scope; final source/translation review, measured calibration/held-out accuracy/performance and M4D–F/M5–M8 remain required.
