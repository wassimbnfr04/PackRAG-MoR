# M4B2 dependency and acceptance preparation

Status: VERIFIED after B1 checkpoint012bb27. Final outcomes and limits are in M4B2_QUERY_IDENTIFIER_METHODS.md and artifacts/v1.3/m4/query-gate-0001/gate.json. The text below records the preparation requirements, not outstanding B2 execution.

Read source paragraphs468–473,521,532,536,540 and998. Raw questions/canonical
text remain unchanged. The normalized query drives deterministic aliases/search;
source IDs and immutable hashes are never destructively normalized. Current
runtime passes raw text to the encoder while paragraph998 passes normalized q;
reconcile this in B2 with a new measured parity reference, preserving prior
reference/output files. Do not relabel historical raw-query embedding results.

Query parameters must use the already validated shared ISO date syntax
YYYY-MM-DD, year1–9999, and existing jurisdiction syntax (two uppercase letters,
optional one-to-three uppercase-alphanumeric subdivision). Reject unpaired
surrogates before UTF8 transport. Python dynamic types must not silently coerce
current-law/string parameters. Empty normalized search input must have a clear
shared contract without adding arbitrary control-character restrictions. The
English product-language requirement is separately completed in M4E.

Use the frozen Unicode15 letter/number/underscore ranges for both alias word
boundaries and word extraction, avoiding platform regex Unicode versions. Test
non-BMP boundaries, overlapping aliases, punctuation and combining marks with
shared expectations. FTS5 unicode61 remains the architecture-mandated independent
tokenizer; no change to that schema or second RRF is permitted.

Inspect all eligible alias targets before local16/global32 caps. Reconcile
cross-pack ambiguity with canonical source identity and preserved origins;
multiple sections of one source and duplicate source bytes must not become
ambiguous just because local IDs/pack versions differ. Different eligible
interpretations of one alias must not silently select the first pack. Known
legal amendment/conflict handling remains C; document any interaction rather
than inventing authority sorting here. Exact hits remain relevant per521/532,
and actual exact-but-insufficient generation must still abstain.

Prepare correctly signed synthetic multi-pack corpora with an ephemeral fixture
signer, no private seed saved: duplicate originals/text across different IDs,
distinct originals sharing alias, source aliases spanning sections, ineligible
alias collisions, cross-pack caps, tied sparse/dense ordering and origins.
Exercise verified registry/retrieval on desktop and actual phone, compare exact
orders/ranks/RRF/caps, and prove ambiguous rejection precedes model generation.
Keep raw/normalized query observations and generator counts explicit. Unit-only
fake encoders can verify mechanics but cannot satisfy real runtime acceptance.

Run all regressions and real LFM/Granite desktop/phone smoke against new input
identities, plus retained trust/security/import/cancellation contracts. Preserve
every failed attempt and repair before C. No release calibration, gold labels,
source truth or performance acceptance is implied by these synthetic cases.
