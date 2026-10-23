# ADR-002 — Conflict-scoped authority interpretation

Status: ADOPTED AND BOUNDED IMPLEMENTATION VERIFIED,9 October2026.
C2b shared40 fixed contracts/19 signed retrieval and tokenizer scenarios, actual
7 runtime cases on desktop and both phone variants, full691 regressions/26 host
methods per variant, retained14 desktop/22 development/17 policy phone gates
and9 October restoration/consent pass. conflict-gate0001 records closure.
The conventions remain implementation-owner clarifications under the authorized
v1.3 mission, not assertions that the supplied architecture or a human legal
reviewer chose them. Synthetic publisher metadata is not legal truth or real
release-source review; arbitrary natural-language conflict detection is not
claimed. M4D evidence selection/after-merge relevance and E presentation remain
separate; no complete product claim follows from this bounded acceptance.

## Evidence and problem

Frozen architecture SHA256
9b02f83b186a5b7f0101add861c6ecb40f5eb0b13016f50fa0c76efc6de07536,
paragraphs390/392/397/519/540, provides nullable authority_rank, canonical_uri,
jurisdiction and article, signed directed relations, eligibility before
retrieval, and authority preference inside a conflict set. It explicitly
prohibits global authority sorting and requires retrieval/pack/chunk ties.
It does not define rank polarity, comparability across independently curated
packs, or a globally unique provision key. Existing validation accepts rank0
through2147483647 and null. No schema extension is needed to interpret those
existing fields conservatively.

## Decisions for C2b

1. A smaller known ordinal is stronger;0 is valid. Null stays unknown.
   Ordinals are comparable only within the same authenticated pack publisher
   key and exact nonnull jurisdiction. The signing key identifies the curator,
   not the original source's legal authority. Builders must document the
   mapping for real packs; synthetic ranks do not validate that mapping.
2. A same-provision scope requires law-domain metadata, a common exact nonnull
   jurisdiction, an exact nonempty canonical_uri and a nonempty normalized
   article identifier. This deliberately prefers false abstention to grouping
   every Article1 or an entire law-number alias. Curator equality is needed for
   comparing ordinals, not for detecting a potentially unresolved conflict
   across curators. Identifiers alone, document
   labels, dates, pack versions and titles never prove equivalence.
3. Authenticated amends/supersedes/exception_to edges can establish a related
   set among already eligible candidates from that pack. Endpoint direction
   matters. Graph expansion remains OFF. Edge confidence is retained as a
   publisher claim, not interpreted as a calibrated probability or an
   independently reviewed legal conclusion. A legal preference requires a full
   publisher assertion: confidence exactly1.0 and explicit-reference or curated
   provenance. Other legal edges expose a related but unresolved set; the value
   is an admission convention, not a tuned relevance threshold or truth score.
4. Supersession can prefer an eligible replacement when the set's authority
   values are comparable and the replacement is not weaker. Amendments and
   exceptions retain the underlying rule because the schema cannot prove a
   complete textual repeal. Required companion evidence must survive later
   selection or the system must abstain; C2b does not silently make a partial
   amendment equivalent to full supersession.
5. Distinct text across original-source editions in an authenticated same-provision scope is a potential
   conflict, not a semantic contradiction classifier. Known comparable
   authority chooses a preferred member; equal known ranks use the unchanged
   retrieval order, then pack_id/chunk_id. Unknown or incomparable authority,
   contradictory directed preferences and directed cycles remain explicitly
   unresolved. No latest-document heuristic fills those gaps.
   Several paragraphs of one original edition are preserved together and do
   not become competing versions just because their text differs. Inconsistent
   ordinal claims within one edition are unresolved. A resolved competing
   edition retains all its retrieved paragraphs; an amendment/exception set
   retains all retrieved members. Exact equal text in the same scope is
   equivalent evidence and does not require inventing an authority rank.
6. Exact alias ambiguity may clear only when every eligible interpretation
   before local/global caps belongs to one resolved provision/relationship
   set. Unrelated repair aliases and distinct provisions remain ambiguous.
   Losing a conflicting interpretation to a cap cannot clear ambiguity.
7. Preference is confined to positions occupied by members of that set;
   unrelated candidates keep their deterministic relevance order and original
   sparse/dense ranks and RRF scores. Conflict metadata is visible in results.

## Acceptance before adoption

C2a must first pass its complete retained gates. C2b then needs independently
specified shared expectations for rank polarity, null/equal values, curator and
jurisdiction boundaries, distinct provisions, high-authority unrelated noise,
directed supersession/amendment/exception, cycles, historical eligibility,
before-cap collisions and caller-order reversal. Signed fixture tests must
exercise both readers and actual retrieval, followed by all regressions and
real desktop/phone LFM smoke. Companion-evidence token/coverage enforcement
must be integrated before C2b can be called verified; it cannot be deferred
while an answer path drops the underlying rule.

Open implementation work: freeze the exact public conflict result contract and
test corpus; reconcile relationship overlaps and deduplicated pack origins.
This implemented policy remains subject to those executable checks. There is no
claim of arbitrary natural-language contradiction detection, legal advice,
release calibration, final product or physical performance acceptance.
