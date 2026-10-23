"""CandidateRelevanceGateV1 on an already ordered, merged and capped pool.

Thresholds are authenticated pack values, never inferred from RRF. This gate
does not establish answerability or measured release calibration.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class RelevanceSignal:
    exact: bool
    sparse_rank: int | None
    dense_rank: int | None
    dense_score: float
    calibrated: bool
    agreed_threshold: float | None
    dense_only_threshold: float | None


def mark_relevance(signals: list[RelevanceSignal]) -> tuple[bool, ...]:
    marked = [item.exact for item in signals]
    top = next((index for index, item in enumerate(signals) if not item.exact), None)
    if top is not None:
        item = signals[top]
        if item.calibrated:
            assert item.agreed_threshold is not None and item.dense_only_threshold is not None
            marked[top] = bool(
                item.sparse_rank is not None and item.dense_rank is not None
                and item.dense_score >= item.agreed_threshold
                or item.dense_rank == 1 and item.dense_score >= item.dense_only_threshold
            )
    return tuple(marked)
