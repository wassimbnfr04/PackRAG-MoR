"""Fixed independent decisions and whole-trial oracles, not model inference."""
import json
from pathlib import Path

import pytest

from product.packrag.config import RuntimeContractError
from product.packrag.selection import SelectionItem, select

CONTRACT = json.loads((Path(__file__).parent / "fixtures/selection-contracts.json").read_text())


def inputs(case):
    # The fixture's symbolic canonical label is a hash-pair stand-in only.
    labels = {row['key']: (row.get('source', row['key']), row.get('canonical', row['key']))
              for row in case['items']}
    return tuple(SelectionItem(row['key'], row.get('position', index),
        labels[row['key']], row.get('source', row['key']),
        (0, row.get('value', -row.get('position', index)), 0, .8),
        (row.get('context', 'same'),),
        tuple(labels.get(key, (key, key)) for key in row.get('required', [])),
        row.get('resolved', True)) for index, row in enumerate(case['items'], 1))


@pytest.mark.parametrize('case', CONTRACT['cases'], ids=lambda row: row['id'])
def test_fixed_selection(case):
    items = inputs(case)
    costs = case.get('costs', {})
    measured = []
    def measure(keys):
        measured.append(keys)
        return tuple(costs.get(','.join(keys), [len(keys)*100, len(keys)*100+100]))
    def run(pool):
        return select(pool, chunk_cap=case.get('chunk_cap', 4), evidence_cap=1200,
                      prefill_cap=1536, measure=measure)
    if 'error' in case:
        with pytest.raises(RuntimeContractError, match='^'+case['error']+'$') as caught:
            run(items)
        if case['error'] in ('INCOMPLETE_LEGAL_CONFLICT_EVIDENCE','LEGAL_CONFLICT_UNRESOLVED'):
            plan=caught.value.selection
            assert plan.admission==case['error'] and plan.keys==() and plan.sources==()
            assert {row.key for row in plan.decisions}=={row.key for row in items}
            assert any(row.reason.startswith(('MANDATORY_','MISSING_','UNRESOLVED_')) for row in plan.decisions)
        return
    plan = run(items)
    assert plan.keys == tuple(case['selected'])
    reasons = {row.key: row.reason for row in plan.decisions}
    assert set(reasons) == {row.key for row in items}
    for key, reason in case.get('reasons', {}).items():
        assert reasons[key] == reason
    assert run(tuple(reversed(items))) == plan
    positions = {row.key: row.position for row in items}
    assert all(list(keys) == sorted(keys, key=positions.get) for keys in measured)
    assert plan.sources == tuple(sorted({row.source for row in items if row.key in plan.keys}))


@pytest.mark.parametrize('cost', [(-1, 100), (100, -1), (True, 100), (100., 100)])
def test_bad_costs_fail_closed(cost):
    item = SelectionItem('a', 1, ('s', 't'), 's', (0, 1., 0, .8), ())
    with pytest.raises(RuntimeContractError, match='INVALID_SELECTION_COST'):
        select((item,), chunk_cap=4, evidence_cap=1200, prefill_cap=1536, measure=lambda _: cost)
