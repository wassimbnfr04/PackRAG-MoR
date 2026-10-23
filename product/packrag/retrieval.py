"""Eligible exact search, FTS5 BM25 and dense dot products with deterministic RRF."""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

from .config import PROFILE, RuntimeContractError
from .packs import VerifiedPack
from .normalization import normalize
from .query_unicode import contains_alias, word_terms
from .temporal import iso_date
from .validity import validity_provenance
from .conflicts import ConflictNode, ConflictEdge, ConflictDecision, resolve_conflicts, resolved_interpretation
from .relevance import RelevanceSignal, mark_relevance
from .evidence import EvidenceOrigin, capture_origin


@dataclass(frozen=True)
class Query:
    raw: str
    as_of: str
    jurisdiction: str | None = None
    current_law: bool = False

    def __post_init__(self):
        if type(self.raw) is not str or any(0xD800 <= ord(char) <= 0xDFFF for char in self.raw):
            raise RuntimeContractError("INVALID_QUERY_TEXT")
        if type(self.as_of) is not str:
            raise RuntimeContractError("INVALID_QUERY_DATE")
        try:
            iso_date(self.as_of)
        except ValueError as error:
            raise RuntimeContractError("INVALID_QUERY_DATE") from error
        if self.jurisdiction is not None and (type(self.jurisdiction) is not str or not re.fullmatch(r"[A-Z]{2}(?:-[A-Z0-9]{1,3})?", self.jurisdiction)):
            raise RuntimeContractError("INVALID_QUERY_JURISDICTION")
        if type(self.current_law) is not bool:
            raise RuntimeContractError("INVALID_QUERY_CURRENT_LAW")
        if not self.normalized:
            raise RuntimeContractError("EMPTY_QUESTION")

    @property
    def normalized(self):
        return normalize(self.raw)


@dataclass(frozen=True)
class Candidate:
    pack: VerifiedPack
    chunk: dict
    exact: bool
    sparse_rank: int | None
    dense_rank: int | None
    dense_cosine: float
    rrf: float
    relevant: bool = False
    origins: tuple[tuple[str, str, str], ...] = ()
    conflicts: tuple[ConflictDecision, ...] = ()
    final_rank: int | None = None
    origin_records: tuple[EvidenceOrigin, ...] = ()

    @property
    def origin_key(self):
        return f"{self.pack.identity[0]}@{self.pack.identity[1]}:{self.pack.identity[2]}#{self.chunk['chunk_id']}"

    @property
    def key(self):
        return (0 if self.exact else 1, -self.rrf, -int(self.exact),
                -self.dense_cosine, self.pack.identity[0], self.chunk["chunk_id"])


def eligible(row: dict, query: Query) -> bool:
    if query.jurisdiction is not None and row["jurisdiction"] != query.jurisdiction:
        return False
    validity = validity_provenance(row)
    start, end = validity["effective_from"], validity["effective_until_excl"]
    if validity["empty_intersection"]:
        return False
    if start and query.as_of < start or end and query.as_of >= end:
        return False
    return not (query.current_law and row["legal_status"] in ("repealed", "superseded"))


def exact_alias_matches(pack: VerifiedPack, query: Query, allowed: set[str]) -> dict[str, set[str]]:
    text = query.normalized
    matches: dict[str, set[str]] = {}
    for alias in pack.aliases:
        value = normalize(alias["normalized_alias"])
        if contains_alias(text, value):
            targets = {alias["target_id"]} if alias["target_type"] == "chunk" else {
                row["chunk_id"] for row in pack.chunks if row["source_id"] == alias["target_id"]
            }
            matches.setdefault(value, set()).update(targets & allowed)
    return matches


def exact_ids(pack: VerifiedPack, query: Query, allowed: set[str]) -> tuple[set[str], bool]:
    matches = exact_alias_matches(pack, query, allowed)
    # Canonical original-byte identity survives different local source IDs.
    ambiguous = any(len({pack.by_id[key]["sha256_original"] for key in keys}) > 1
                    for keys in matches.values())
    return set().union(*matches.values()) if matches else set(), ambiguous


def retrieve_pack(pack: VerifiedPack, query: Query, vector: np.ndarray, *, limit: bool = True) -> tuple[list[Candidate], bool]:
    rows = [row for row in pack.chunks if eligible(row, query)]
    allowed = {row["chunk_id"] for row in rows}
    exact, ambiguous = exact_ids(pack, query, allowed)
    terms = word_terms(query.normalized)
    sparse = []
    if terms:
        expression = " OR ".join('"' + word + '"' for word in terms)
        # Filter eligibility before retaining the top 24, not after a SQL LIMIT.
        hits = pack.db.execute(
            "SELECT c.chunk_id,bm25(chunks_fts) AS score FROM chunks_fts "
            "JOIN chunks c ON c.rowid=chunks_fts.rowid WHERE chunks_fts MATCH ? "
            "ORDER BY score ASC,c.chunk_id ASC", (expression,),
        ).fetchall()
        sparse = [row["chunk_id"] for row in hits if row["chunk_id"] in allowed][:PROFILE["sparse_candidate_k"]]
    dense_scores = {row["chunk_id"]: float(np.dot(pack.vectors[row["dense_row"]], vector)) for row in rows}
    dense = sorted(dense_scores, key=lambda key: (-dense_scores[key], key))[:PROFILE["dense_candidate_k"]]
    sr = {key: rank for rank, key in enumerate(sparse, 1)}
    dr = {key: rank for rank, key in enumerate(dense, 1)}
    candidates = []
    for key in set(sparse) | set(dense) | exact:
        rrf = sum(1 / (PROFILE["rrf_k"] + rank) for rank in (sr.get(key), dr.get(key)) if rank is not None)
        candidates.append(Candidate(pack, pack.by_id[key], key in exact, sr.get(key), dr.get(key),
                                    dense_scores[key], rrf, origins=(pack.identity,)))
    candidates.sort(key=lambda item: item.key)
    if limit:
        candidates = local_fused_limit(candidates)
    # Calibrated relevance belongs to the merged/global-capped pool, not each pack.
    output = [Candidate(**{**item.__dict__, "relevant": item.exact}) for item in candidates]
    return output, ambiguous


def local_fused_limit(candidates: list[Candidate]) -> list[Candidate]:
    """Union all exact hits with each pack's independently ranked top16 RRF hits.

    A chunk in both lists appears once and consumes one RRF slot. A pure alias
    hit outside RRF does not consume a slot. Preserve conflict-scoped member
    preference without moving unrelated entries or fabricating a score.
    """
    groups = {}
    for item in candidates:
        groups.setdefault(item.pack.identity, []).append(item)
    admitted = set()
    for rows in groups.values():
        fused = sorted((item for item in rows if item.sparse_rank is not None or item.dense_rank is not None),
                       key=lambda item: (-item.rrf, -int(item.exact), -item.dense_cosine,
                                         item.pack.identity[0], item.chunk["chunk_id"]))
        decisions = tuple(dict.fromkeys(d for item in rows for d in item.conflicts if d.resolved))
        for decision in decisions:
            positions = [i for i, item in enumerate(fused) if item.origin_key in decision.members]
            members = sorted((fused[i] for i in positions), key=lambda item: decision.retained.index(item.origin_key))
            for index, item in zip(positions, members, strict=True):
                fused[index] = item
        admitted.update(item.origin_key for item in fused[:PROFILE["per_pack_fused_cap"]])
        admitted.update(item.origin_key for item in rows if item.exact)
    return [item for item in candidates if item.origin_key in admitted]


def retrieve(packs: tuple[VerifiedPack, ...], query: Query, vector: np.ndarray) -> tuple[list[Candidate], bool]:
    if vector.shape != (384,) or not np.isfinite(vector).all() or abs(float(np.linalg.norm(vector)) - 1) > .01:
        raise RuntimeContractError("Invalid query embedding")
    all_candidates = []
    interpretations: dict[str, set[str]] = {}
    for pack in packs:
        allowed = {row["chunk_id"] for row in pack.chunks if eligible(row, query)}
        prefix = f"{pack.identity[0]}@{pack.identity[1]}:{pack.identity[2]}#"
        for alias, keys in exact_alias_matches(pack, query, allowed).items():
            interpretations.setdefault(alias, set()).update(prefix + key for key in keys)
        candidates, _ = retrieve_pack(pack, query, vector, limit=False)
        all_candidates.extend(candidates)
    all_candidates.sort(key=lambda item: item.key)
    nodes = [ConflictNode(item.origin_key, item.chunk["sha256_original"], item.chunk["text_sha256"],
        item.pack.manifest["domain"], item.pack.manifest["publisher"]["key_id"], item.chunk["jurisdiction"],
        item.chunk["canonical_uri"], item.chunk["article"], item.chunk["authority_rank"], index)
        for index, item in enumerate(all_candidates)]
    edges = []
    for pack in packs:
        prefix = f"{pack.identity[0]}@{pack.identity[1]}:{pack.identity[2]}#"
        edges.extend(ConflictEdge(prefix + edge["from_chunk_id"], prefix + edge["to_chunk_id"],
            edge["relation_type"], edge["provenance"], edge["confidence"]) for edge in pack.relations)
    decisions = resolve_conflicts(nodes, edges)
    by_key = {node.key: node for node in nodes}
    ambiguous = any(len({by_key[key].original for key in keys}) > 1 and not resolved_interpretation(keys, decisions)
                    for keys in interpretations.values())
    decision_by_key = {key: decision for decision in decisions for key in decision.members}
    retained = []
    for item in all_candidates:
        decision = decision_by_key.get(item.origin_key)
        if decision is None or item.origin_key in decision.retained:
            retained.append(Candidate(**{**item.__dict__, "conflicts": (decision,) if decision else ()}))
    # Move only members into their own occupied slots; unrelated relevance order,
    # ranks, RRF and numerical scores are never replaced by authority.
    for decision in decisions:
        if not decision.resolved:
            continue
        positions = [index for index, item in enumerate(retained) if item.origin_key in decision.members]
        members = sorted((retained[index] for index in positions), key=lambda item: decision.retained.index(item.origin_key))
        for index, item in zip(positions, members, strict=True):
            retained[index] = item
    capped = local_fused_limit(retained)
    dedup: dict[tuple[str, str], Candidate] = {}
    for candidate in capped:
        candidate=Candidate(**{**candidate.__dict__, 'origin_records': (capture_origin(candidate),)})
        identity = candidate.chunk["sha256_original"], candidate.chunk["text_sha256"]
        if identity in dedup:
            previous = dedup[identity]
            dedup[identity] = Candidate(**{**previous.__dict__,
                                          "relevant": previous.relevant or candidate.relevant,
                                          "conflicts": tuple(dict.fromkeys(previous.conflicts + candidate.conflicts)),
                                          "origins": tuple(dict.fromkeys(previous.origins + candidate.origins))})
            dedup[identity]=Candidate(**{**dedup[identity].__dict__,
                'origin_records':previous.origin_records+candidate.origin_records})
        else:
            dedup[identity] = candidate
    merged = list(dedup.values())[:PROFILE["cross_pack_pool_limit"]]
    signals = []
    for item in merged:
        calibration = item.pack.manifest["calibration"]
        signals.append(RelevanceSignal(item.exact, item.sparse_rank, item.dense_rank, item.dense_cosine,
            calibration.get("status", "CALIBRATED") != "UNCALIBRATED", calibration["min_agreed_dense_cosine"],
            calibration["min_dense_only_cosine"]))
    flags = mark_relevance(signals)
    return [Candidate(**{**item.__dict__, "relevant": flag, "final_rank": index})
            for index, (item, flag) in enumerate(zip(merged, flags, strict=True), 1)], ambiguous
