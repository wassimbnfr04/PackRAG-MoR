"""Conservative signed-metadata interpretation; no graph expansion or legal truth oracle."""
from __future__ import annotations

from dataclasses import dataclass

from .normalization import normalize


@dataclass(frozen=True)
class ConflictNode:
    key: str
    original: str
    text: str
    domain: str
    publisher_key: str
    jurisdiction: str | None
    canonical_uri: str | None
    article: str | None
    authority: int | None
    order: int

    @property
    def canonical(self):
        return self.original, self.text


@dataclass(frozen=True)
class ConflictEdge:
    source: str
    target: str
    kind: str
    provenance: str
    confidence: float


@dataclass(frozen=True)
class ConflictDecision:
    members: tuple[str, ...]
    state: str
    reason: str
    preferred: str | None
    retained: tuple[str, ...]
    required: tuple[tuple[str, str], ...]

    @property
    def resolved(self):
        return self.state != "UNRESOLVED"


LEGAL_EDGES = frozenset(("amends", "supersedes", "exception_to"))


def resolve_conflicts(nodes: list[ConflictNode], edges: list[ConflictEdge]) -> tuple[ConflictDecision, ...]:
    """Nodes are already eligible retrieval hits; this function cannot add a hit."""
    ordered = sorted(nodes, key=lambda node: (node.order, node.key))
    by_key = {node.key: node for node in ordered}
    assert len(by_key) == len(nodes), "Duplicate conflict node"
    parent = {node.key: node.key for node in ordered}

    def root(key):
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    def join(a, b):
        a, b = root(a), root(b)
        if a != b:
            parent[max(a, b)] = min(a, b)

    scopes = {}
    for node in ordered:
        article = normalize(node.article) if node.article else ""
        if node.domain == "law" and node.jurisdiction is not None and node.canonical_uri and article:
            scope = node.jurisdiction, node.canonical_uri, article
            if scope in scopes:
                join(node.key, scopes[scope])
            else:
                scopes[scope] = node.key
    legal = []
    for edge in edges:
        if edge.kind not in LEGAL_EDGES or edge.source not in by_key or edge.target not in by_key:
            continue
        a, b = by_key[edge.source], by_key[edge.target]
        if a.domain == b.domain == "law" and a.jurisdiction is not None and a.jurisdiction == b.jurisdiction:
            legal.append(edge)
            join(a.key, b.key)
    groups = {}
    for node in ordered:
        groups.setdefault(root(node.key), []).append(node)
    decisions = []
    for members in groups.values():
        keys = tuple(node.key for node in members)
        links = [edge for edge in legal if edge.source in keys and edge.target in keys]
        if len(members) < 2 and not links:
            continue
        # Several paragraphs of one edition are not conflicting versions.
        if len({node.original for node in members}) == 1 and not links:
            continue

        def unresolved(reason):
            return ConflictDecision(keys, "UNRESOLVED", reason, None, keys, ())

        if not links and len({node.text for node in members}) == 1:
            decisions.append(ConflictDecision(keys, "EQUIVALENT", "SAME_PROVISION_EXACT_TEXT", keys[0], keys, ()))
            continue
        if any(edge.confidence != 1.0 or edge.provenance not in ("explicit-reference", "curated") for edge in links):
            decisions.append(unresolved("RELATION_NOT_FULL_PUBLISHER_ASSERTION"))
            continue
        if any(node.authority is None for node in members):
            decisions.append(unresolved("UNKNOWN_AUTHORITY"))
            continue
        if len({node.publisher_key for node in members}) != 1:
            decisions.append(unresolved("INCOMPARABLE_CURATORS"))
            continue
        edition_ranks = {}
        for node in members:
            edition_ranks.setdefault(node.original, set()).add(node.authority)
        if any(len(values) != 1 for values in edition_ranks.values()):
            decisions.append(unresolved("INCONSISTENT_EDITION_AUTHORITY"))
            continue
        if any(by_key[edge.source].authority > by_key[edge.target].authority for edge in links):
            decisions.append(unresolved("WEAKER_DECLARED_REPLACEMENT"))
            continue
        outgoing = {key: set() for key in keys}
        indegree = {key: 0 for key in keys}
        for edge in links:
            if edge.target not in outgoing[edge.source]:
                outgoing[edge.source].add(edge.target)
                indegree[edge.target] += 1
        ready = [key for key in keys if indegree[key] == 0]
        topology = []
        while ready:
            ready.sort(key=lambda key: (by_key[key].authority, by_key[key].order, key))
            key = ready.pop(0)
            topology.append(key)
            for target in sorted(outgoing[key]):
                indegree[target] -= 1
                if indegree[target] == 0:
                    ready.append(target)
        if len(topology) != len(keys):
            decisions.append(unresolved("DIRECTED_CYCLE"))
            continue
        companion = any(edge.kind in ("amends", "exception_to") for edge in links)
        superseded = {edge.target for edge in links if edge.kind == "supersedes"}
        possible = [node for node in members if node.key not in superseded]
        # A cycle-free finite graph always has a surviving replacement.
        preferred = min(possible, key=lambda node: (node.authority, topology.index(node.key), node.order, node.key))
        if companion:
            retained = tuple(topology)
            required = tuple(sorted({node.canonical for node in members}))
        else:
            retained = tuple(node.key for node in members if node.original == preferred.original and node.key not in superseded)
            required = tuple(sorted({by_key[key].canonical for key in retained}))
        decisions.append(ConflictDecision(keys, "RESOLVED_RELATION" if links else "RESOLVED_AUTHORITY",
            "RETAIN_BASE_AND_COMPANIONS" if companion else "PREFERRED_EDITION", preferred.key, retained, required))
    return tuple(decisions)


def resolved_interpretation(keys: set[str], decisions: tuple[ConflictDecision, ...]) -> bool:
    """All pre-cap alias targets must belong to one resolved set."""
    return any(decision.resolved and keys <= set(decision.members) for decision in decisions)
