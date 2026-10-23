# C2a authenticated source metadata methods

Status: VERIFIED after C1 checkpoint4b93b85; source-metadata-gate0001 binds this bounded acceptance. Fixture construction/loader
assertions pass in source-metadata-fixtures0003; run0005 passes618 Python tests,
both builds0009/0010 pass24 host methods, and smoke0005 passes14 real desktop
cases. Development phone gate passes20 methods598.249s; all20 structured results
are saved. Compiled production-policy gate passes15 methods276.503s; all15 final
structured results are saved. Restoration0006 passes one method/four copy-consent checks3.601s; final
closure preflight passes132 runtime/429 Android inputs,587 historical identities
and all retained B2/C1 saved-output/APK/corpus/native identities. Full C2 authority behavior and
complete v1.3 product acceptance are not established here.

Both authenticated pack readers now expose the existing authority_rank,
document_version, issued_at and article fields plus typed directed relations
with provenance/confidence. They preserve nulls, empty strings, Unicode values,
zero/max-int rank and fractional timestamps. Source metadata carries the signed
pack publisher key ID; it identifies the curator/signing namespace, not a proof
that the original source publisher has legal authority. Python copies exposed
relation dictionaries so a result consumer cannot mutate verified relation
metadata. Kotlin returns only incoming/outgoing edges touching the cited chunk.
No relation edge adds a retrieval candidate or fabricated RRF score.

Desktop candidate/selected/cited records contain this metadata. Android actual
cited SourceRecord contains it. Actual smoke assertions require the original
walking-pack unknown fields remain null, no relation is invented, and the
publisher key ID matches its authenticated manifest. Android source-screen
presentation is separately E. C2a introduces no authority-rank convention,
global sort, alias ambiguity override, graph expansion, recency inference,
model/template/native/decoding change or semantic source-truth claim.

The signed metadata corpus derives canonical text/IDs/intervals from the
immutable C1 synthetic corpus, using a fresh ephemeral signer never saved.
Eight independently specified field sets cover null/empty values, ranks0/1/2/4/
2147483647, non-SemVer document labels, French/Arabic/supplementary identifiers,
date/timestamp/fractional timestamp syntax. Five edges are narrow→baseline
amends, future→baseline supersedes, unknown→baseline exception_to,
historical→baseline cites, baseline→narrow see_also. Confidence values are
1/.75/.5/0/1, with explicit-reference/curated/structure provenance. They test
preservation and direction only; they do not prove a real legal relationship or
calibrated probability. Future/ineligible endpoints may appear in provenance;
they must not enter the generator merely because an edge exists.

Fixture0001 authenticated eight metadata cases but reused C1 document vectors
without specifying section/article precedence. The first correction called
that an established recipe mismatch, which was too strong: a section-first
policy could retain those inputs. Its CLARIFICATION.md preserves this correction
of the diagnosis; no unit/build/phone acceptance ran against0001. Fixture0002
regeneration failed because nullable article was accidentally passed as the
contextual-prefix argument, before writing a final dense payload/pack/test
assets. Both drafts remain separate, unaccepted preparation.

Fresh0003 uses the fixed profile's title/newline/section-or-article/newline/
contextual-prefix/newline/canonical-text recipe. For this legal fixture, a
nonempty article is the heading, otherwise section; contextual prefix is the
empty string. Exact inputs are saved in embedding-inputs.json with a bound hash.
All eight document vectors are freshly computed by pinned Granite. The unchanged
normalized query's previous actual vector is reused explicitly; Android runs
the actual encoder and compares it. Article changes require an FTS rebuild, so
new numeric ranks/scores are separately measured; retained C1/B packs/references
are not rewritten. Independently fixed eligible sets and conservative ambiguity
expectations remain identical to C1. Numeric ordering is a desktop parity oracle,
not independent legal/semantic gold. New12 scenarios require exact candidate/
rank/RRF agreement and≤1e-4 embedding/cosine error on the phone.

All corpus fields are synthetic, UNCALIBRATED and unrelated to release law or
repair demonstrators. Actual LFM desktop/phone generation remains the separate
retained acceptance; controlled desktop serialization tests do not replace it.
Mobile data remains ON; app INTERNET permission stays absent. Owner assets and
registry are preserved. Instrumentable Android Debug-signed demo tests compiled
production policy, not final nondebuggable release or resource acceptance.

Development observed results:8 metadata cases/5 directed relations/12 eligible
retrieval scenarios pass, maximum absolute embedding error9.313225746154785e-8
and cosine error1.2100272628323694e-7. Retained alias ambiguity emits0 tokens
and has0 prefill tokens (model load is explicitly not excluded); expired
collision accepts the actual74°C[S1] answer,363 prefill/196 evidence/165 emitted
tokens,129270.92414ms total. Native cancellation returns in102.950703ms and
actual recovery passes; closed-handle/idempotent lifecycle checks pass.
Retained real cited smoke uses389 prefill/234 evidence/174 emitted tokens,
170390.488203ms including10451.632109ms lazy initialization,
96849.676172ms prefill and62993.66625ms decode. No-pack avoids generator load;
unrelated query rejects before generation. Actual citations assert unknown/open
validity and exact authenticated publisher metadata. These timings describe
these functional runs, not resource acceptance, peak memory or a causal
hardware/software comparison. Both original canonical text and all prior
experiment files remain unchanged.

Production-policy release-core actual generation accepts74°C[S1] and exact
canonical text, with authenticated metadata and unknown/open validity asserted;
194728.233008ms including lazy initialization/179 emitted terminal-inclusive
tokens. Unknown publishers, uncalibrated packs and pack-supplied trust changes
reject while previous active originals remain intact. Its retained raw limits
string says DEBUG artifact; the demo is indeed instrumentable and Android Debug
signed, while a separate test verifies the compiled production policy. This
does not substitute for final nondebuggable release or measured calibration.
