# C2 design audit before implementation

Status: C1 verified at4b93b85; C2a's integrated metadata gate is verified.
Conflict behavior C2b remains preparation only. ADR-002-v13-conflict-scope.md
records a concrete PROPOSED convention and its required executable checks;
there is no accepted C2b behavior or complete C2 test claim here.

Frozen evidence: paragraph519 prohibits global authority sorting.540 scopes
authority to same provisions/propositions, explicit amendment/supersession/
exception links, or detected conflicts, with relevance primary for unrelated
candidates and deterministic retrieval/pack/chunk ties. The source schema390
has nullable authority_rank/document_version/canonical_uri/jurisdiction/status;
392 has article/locator;397 has typed directed relations with provenance and
confidence; aliases carry article-id/law-number/error-code/acronym/synonym.
Existing metadata validation allows authority integers0..2147483647 and null.
The text does not specify numeric rank polarity or cross-publisher comparability.

Required implementation decisions before code:

- Record a source-bound ADR for authority rank convention and comparability.
  Pack metadata is a publisher claim, not proof of legal authority. Missing rank
  must remain unknown; do not invent a rank from recency, pack version, title,
  URL, retrieved_at or publication time.
- Define deterministic same-provision scope using authenticated identifiers
  and source metadata. A bare Article1 or common law-number alias cannot make
  every article, jurisdiction or unrelated law a single conflict. Arbitrary
  repair identifier collisions from B2 must remain ambiguous.
- Load authenticated authority/document/version/article and relation metadata
  on Android as well as desktop, without schema/format migration. Relations
  already have validated endpoints. An authenticated edge does not certify its
  real-world truth; fixtures and real release-source review remain distinct.
- Distinguish amendment/supersession preference from exception coverage.
  An exception must not automatically erase its underlying rule. Do not infer
  a full repeal from a partial amendment or pick the most recent pack globally.
- Handle unknown/incomparable authority, cycles and unresolved conflicts
  explicitly. Aliases may cease being ambiguous only under the documented
  verified relationship/scope policy; never select whichever pack was passed
  first. Preserve canonical identities and all pack origins.
- Keep graph candidate expansion off. Resolving metadata among already
  eligible retrieval candidates is not permission to inject linked chunks,
  fabricate RRF or turn on benchmark Graph-Lite in the product.
- Apply interval/current-law/jurisdiction filtering before any conflict
  interpretation and caps. Check before-cap alias interpretation cannot lose
  an unresolved collision merely because local16/global32 discarded a row.
  Keep fixed ranks/scores and deterministic unrelated-candidate ordering.

C2 fixtures must independently specify desired sets/preferences and negatives;
desktop numeric output alone is only a parity oracle. Include equal/unknown
authority, different publishers/jurisdictions, unrelated high-authority noise,
explicit supersession/amendment/exception, historical dates and caller-order
reversal. Retain C1/B/security/native cancellation and real desktop/phone flow.
Final evidence coverage and the after-merge paragraph532 relevance gate remain D;
do not silently mark the whole retrieval paragraphs verified here.
