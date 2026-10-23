"""Deterministic atomic selection from an already admitted retrieval pool.

Costs are supplied for the complete, ordered trial; they are never summed from
per-item estimates. This module cannot retrieve, score, render or invent evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .config import RuntimeContractError


@dataclass(frozen=True)
class SelectionItem:
    key: str
    position: int
    canonical: tuple[str, str]
    source: str
    value: tuple[int, float, int, float]
    redundancy: tuple
    required: tuple[tuple[str, str], ...] = ()
    resolved: bool = True


@dataclass(frozen=True)
class SelectionDecision:
    key: str
    reason: str
    trial: tuple[str, ...] = ()
    representative: str | None = None
    evidence_tokens: int | None = None
    prefill_tokens: int | None = None


@dataclass(frozen=True)
class SelectionPlan:
    keys: tuple[str, ...]
    decisions: tuple[SelectionDecision, ...]
    sources: tuple[str, ...]
    admission: str = 'READY'


class SelectionFailure(RuntimeContractError):
    def __init__(self,state,selection):
        super().__init__(state)
        self.selection=selection


def select(items: tuple[SelectionItem, ...], *, chunk_cap: int, evidence_cap: int,
           prefill_cap: int, measure: Callable[[tuple[str, ...]], tuple[int, int]]) -> SelectionPlan:
    """Keep pool order, permit source coverage only within contiguous value ties.

Required members are protected from ordinary literal redundancy. A mandatory
bundle which is missing, unresolved or over a cap rejects the request rather
than emitting a partial interpretation. Repeated identical keys are harmless;
inconsistent keys/positions are invalid input. Every unique key gets a decision.
"""
    if min(chunk_cap, evidence_cap, prefill_cap) <= 0:
        raise RuntimeContractError("INVALID_SELECTION_CAPS")
    by_key = {}
    by_position = {}
    for item in items:
        if item.position < 1 or not item.key or not item.source:
            raise RuntimeContractError("INVALID_SELECTION_POOL")
        if item.key in by_key:
            if item != by_key[item.key]:
                raise RuntimeContractError("INVALID_SELECTION_POOL")
            continue
        if item.position in by_position:
            raise RuntimeContractError("INVALID_SELECTION_POOL")
        by_key[item.key] = item
        by_position[item.position] = item
    ordered = sorted(by_key.values(), key=lambda item: item.position)
    canonical = {}
    for item in ordered:
        canonical.setdefault(item.canonical, item.key)
    protected = {pair for item in ordered for pair in item.required}
    # Roots with required members are protected even if a malformed caller did
    # not list the root itself in its relationship's required canonical set.
    mandatory = {item.key for item in ordered if item.required or item.canonical in protected}
    selected = set()
    decisions = {}

    def trial_keys(keys):
        return tuple(item.key for item in ordered if item.key in keys)

    def fail(state,key,reason,trial=(),cost=None):
        decisions[key]=SelectionDecision(key,reason,trial,evidence_tokens=cost[0] if cost else None,
            prefill_tokens=cost[1] if cost else None)
        values=tuple(decisions.get(item.key,SelectionDecision(item.key,'NOT_CONSIDERED_AFTER_REJECTION')) for item in ordered)
        raise SelectionFailure(state,SelectionPlan((),values,(),state))

    def bundle(root):
        pending = [root.key]
        result = set()
        while pending:
            key = pending.pop()
            if key in result:
                continue
            result.add(key)
            item = by_key[key]
            if not item.resolved:
                fail('LEGAL_CONFLICT_UNRESOLVED',key,'UNRESOLVED_CONFLICT',trial_keys(result | selected))
            for pair in item.required:
                companion = canonical.get(pair)
                if companion is None:
                    fail('INCOMPLETE_LEGAL_CONFLICT_EVIDENCE',key,'MISSING_REQUIRED_MEMBER',trial_keys(result | selected))
                pending.append(companion)
        return result

    # Process contiguous groups independently. A lower-valued row cannot jump
    # over a higher-valued row or a conflict-preferred occupied slot.
    cursor = 0
    while cursor < len(ordered):
        group = [ordered[cursor]]
        cursor += 1
        while (cursor < len(ordered) and group[0].key not in mandatory
               and ordered[cursor].key not in mandatory
               and ordered[cursor].value == group[0].value):
            group.append(ordered[cursor])
            cursor += 1
        while group:
            sources = {by_key[key].source for key in selected}
            root = min(group, key=lambda item: (item.source in sources, item.position))
            group.remove(root)
            if root.key in selected:
                decisions.setdefault(root.key, SelectionDecision(root.key, "REQUIRED_COMPANION", trial_keys(selected)))
                continue
            if root.key not in mandatory:
                duplicate = next((item for item in ordered if item.key in selected
                                  and item.key not in mandatory and item.canonical == root.canonical
                                  and item.source == root.source and item.redundancy == root.redundancy), None)
                if duplicate is not None:
                    decisions[root.key] = SelectionDecision(root.key, "LITERAL_DUPLICATE", representative=duplicate.key)
                    continue
            members = bundle(root)
            trial = trial_keys(selected | members)
            if len(trial) > chunk_cap:
                if members & mandatory:
                    fail('INCOMPLETE_LEGAL_CONFLICT_EVIDENCE',root.key,'MANDATORY_CHUNK_CAP',trial)
                decisions[root.key] = SelectionDecision(root.key, "CHUNK_CAP", trial)
                continue
            evidence, prefill = measure(trial)
            if type(evidence) is not int or type(prefill) is not int or min(evidence, prefill) < 0:
                raise RuntimeContractError("INVALID_SELECTION_COST")
            if evidence > evidence_cap or prefill > prefill_cap:
                if members & mandatory:
                    fail('INCOMPLETE_LEGAL_CONFLICT_EVIDENCE',root.key,'MANDATORY_TOKEN_CAP',trial,(evidence,prefill))
                decisions[root.key] = SelectionDecision(root.key, "TOKEN_CAP", trial,evidence_tokens=evidence,prefill_tokens=prefill)
                continue
            for key in members - selected:
                decisions[key] = SelectionDecision(key, "SELECTED" if key == root.key else "REQUIRED_COMPANION", trial,
                    evidence_tokens=evidence,prefill_tokens=prefill)
            selected.update(members)
    keys = trial_keys(selected)
    return SelectionPlan(keys, tuple(decisions[item.key] for item in ordered),
                         tuple(sorted({by_key[key].source for key in keys})))
