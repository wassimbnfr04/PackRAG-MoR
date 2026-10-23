# Query and identifier methods

Status: B2 VERIFIED.548 Python tests,22 host methods per variant,14 real desktop
cases,18 development phone methods730.981s and13 compiled production-policy
phone methods285.015s pass. All31 structured gate results are saved. Development
restoration passes one method/four consent checks3.936s. Final identity preflight
passes417 Android inputs per variant,121 public runtime inputs,587 historical
identities, exact APKs and unchanged JNI. query-gate0001 binds these outcomes.
Full M4 and product acceptance remain incomplete. Work crosses midnight6–7 October.

## Input and normalization contract

Queries retain raw user text. A separate normalized copy uses verified B1
Unicode15 NFKC/default-lower/Arabic-mark removal/whitespace semantics. It drives
the encoder and deterministic search. Dates use the existing strict shared
YYYY-MM-DD parser with valid Gregorian dates and years1–9999. Jurisdiction
uses the manifest syntax: two uppercase letters, optionally a hyphen and one to
three uppercase-alphanumeric subdivision characters. No implicit string/type
coercion is permitted in Python; Kotlin signatures already require strings and
Boolean values. Lone surrogates and empty normalized search input are rejected.
Raw NUL is not arbitrarily prohibited in this increment; final prompt/control
admission is D. English product-language admission is E.

Source998 explicitly supplies normalized q to the encoder. The earlier runtime
had used raw input. This change creates new measured normalized-input references
without modifying old raw-input tokenizer/vector/prompt outputs. Retained M2
component parity still uses its explicitly supplied raw-input vectors; it must
not be represented as proof of the new runtime's normalized embedding path.
The new parity method actually encodes normalized inputs on Android and compares
them with new actual desktop Granite vectors. Raw question text still goes to
the original user prompt; source IDs/canonical text are not lowercased.

## Alias boundaries, interpretations and provenance

Frozen Unicode15 letter/number/underscore properties replace platform regex
properties for word extraction and both alias boundaries. Terms sort by scalar
codepoints on both platforms. Literal alias scanning permits a later valid match
when an earlier occurrence is embedded inside a word. Combining marks are not
word characters under this existing Python-style contract; supplementary letters
are. FTS5 unicode61/remove_diacritics2 remains unchanged and independently
tokenizes the bound OR expression. No generator query rewriting is introduced.

Before top-k/caps, each pack resolves all matched aliases to eligible chunks.
One normalized alias pointing to different eligible original-source hashes is
ambiguous across the active set. Multiple sections of one source, duplicate
original bytes with different local source IDs, and one question naming several
different aliases do not manufacture ambiguity. Original hashes are verified
signed metadata; synthetic originals without snapshots do not certify external
source truth. Existing ambiguity handling is extended across packs, with the
shared IDENTIFIER_AMBIGUOUS state. Explicit legal amendment/conflict resolution
is separately required in C; this conservative behavior is not an authority sort.

Per-pack sparse/dense24, local RRF60, local16 and merged32 limits are retained.
There is no second RRF. Deduplication uses original source hash plus canonical
text hash. The best deterministic representative retains ranks/scores; each
unique pack/version/manifest origin appears once in representative-ranking order.
Exact hits remain relevant per521/532 and still require actual semantic evidence;
the retained real exact-but-insufficient desktop case continues abstaining.

## Signed corpus and independent limits

query-identifier-fixtures0001 contains eight newly signed synthetic packs, with
an ephemeral signer whose private seed is not saved. Primary has44 chunks,
twin44 with different local IDs but duplicate originals/text, distinct42, source
alias2 sections, within-pack duplicate2 locators, collision1, expired1 and lost
collision1. Every pack uses the fixed schema/profile and UNCALIBRATED development
metadata; numeric calibration is not invented. KDX vectors actually come from
the pinned Granite document-input recipe, not a fake encoder.

Ten new measured desktop retrieval references cover normalized fullwidth query,
different-source ambiguity, duplicate originals/different IDs, multi-section
source alias, within-pack unique origins, expired collision,32-cap, ambiguity
where a matched target is discarded by local cap, several distinct aliases and
identifier-not-substring. Their expected ambiguity/cap/duplicate/boundary
constraints are explicitly asserted during fixture construction. Candidate order,
ranks and numeric references are desktop implementation results for cross-platform
comparison; they are not independent human semantic labels or release gold.
The previously tested RRF/eligibility contracts remain mandatory regressions.

Shared input corpus has28 query cases, five word cases and11 alias-boundary cases.
Python adds seven dynamic-type negatives and exhaustively compares frozen word
membership with pinned Unicode15 categories. Invalid dates include compact/week
syntax, signed/zero years, nonexistent days, trailing space and zero month.
Raw supplementary characters are accepted; lone high/low surrogates rejected.
New signed orchestration tests compare all candidate fields and reversed caller
pack order, with ambiguity proving that a fail-on-call generator is never invoked.
Stored query vectors in those unit/adjacent tests do not rerun the encoder.

## Physical execution and observations

run0003 passes548 Python tests and587 immutable historical identities. Both
builds0005/0006 pass22 host methods. Desktop smoke0003 passes14 real cases with
owned-server cleanup after the normalized encoder-input change. New phone parity
passes all28/5/11 shared cases and ten actual normalized-Granite retrieval cases,
with exact candidate order/ranks/RRF/origins. Maximum embedding error is
1.4528632164001465e-7 and cosine error1.789288387454846e-7, within1e-4.
The separately saved observed JSON records the intermediate observation; final
JSON and successful whole-gate instrumentation are retained alongside it.

New actual ProductSession method returns ambiguous with zero emitted/prefill
tokens and no selected evidence. Model loading is explicitly not excluded: the
current session initializes model assets before the retrieval rejection. After
deactivating the real collision, expired collision remains active but ineligible;
actual generation accepts the cited74°C answer and verified canonical/source
identity. Its trace has363prefill/196evidence/165emitted including terminal,
207934.815703ms total,106898.851406ms prefill and100598.252656ms decode.
These functional observations do not establish accepted latency, per-question
memory/thermal peaks or a causal hardware/software bottleneck.

Duplicate TestRunner log filters initially hid INFO progress; a single V filter
fixes the read-only observer. Empty earlier tails were not missing execution.
A host process-inventory attempt was sandbox-denied; ADB provided availability
and progress, with no permission/configuration change. Raw observations and their
limits are retained. The phone's mobile data stays ON, owner assets/registry are
preserved and no raw reasoning is persisted. No airplane, final release signing,
calibration, source review, multilingual generation or PackBench claim is made.
