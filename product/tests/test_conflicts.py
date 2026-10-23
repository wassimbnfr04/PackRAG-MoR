"""Independent fixed conflict outcomes and input-order invariance."""
from dataclasses import asdict
import json
from pathlib import Path
import pytest
from product.packrag.conflicts import ConflictNode, ConflictEdge, resolve_conflicts, resolved_interpretation

CASES = json.loads((Path(__file__).parent / "fixtures/conflict-contracts.json").read_text())["cases"]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_shared_conflict_contract_and_caller_order(case):
    nodes = [ConflictNode(**row) for row in case["nodes"]]
    edges = [ConflictEdge(**row) for row in case["edges"]]
    actual = resolve_conflicts(nodes, edges)
    # JSON converts tuple-owned public values to arrays for the shared contract.
    assert json.loads(json.dumps([asdict(row) for row in actual])) == case["expected"]
    assert resolve_conflicts(list(reversed(nodes)), list(reversed(edges))) == actual
    if case["alias_keys"] is not None:
        assert resolved_interpretation(set(case["alias_keys"]), actual) == case["expected_alias_resolved"]
