"""Independently fixed gate expectations; no actual-model/calibration claim."""
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from product.packrag.relevance import RelevanceSignal, mark_relevance
from product.packrag.retrieval import Candidate, local_fused_limit

CASES=json.loads((Path(__file__).parent/'fixtures/relevance-contracts.json').read_text())['cases']

@pytest.mark.parametrize('case',CASES,ids=lambda c:c['id'])
def test_independently_fixed_merged_relevance(case):
    assert list(mark_relevance([RelevanceSignal(**row) for row in case['signals']]))==case['expected']

def item(key,score,*,exact=False,fused=True,pack='pack'):
    owner=SimpleNamespace(identity=(pack,'1.0.0','manifest'))
    return Candidate(owner,dict(chunk_id=key),exact,1 if fused else None,1 if fused else None,.5,score)

def test_exact_outside_fused_cap_preserves_all_sixteen_rrf_hits():
    rows=[item('alias-only',0,exact=True,fused=False)]+[item(str(i),1/(i+1)) for i in range(20)]
    actual=local_fused_limit(rows)
    assert [c.chunk['chunk_id'] for c in actual]==['alias-only']+[str(i) for i in range(16)]

def test_exact_and_rrf_overlap_uses_one_fused_slot_and_one_record():
    rows=[item('0',1,exact=True)]+[item(str(i),1/(i+1)) for i in range(1,20)]
    assert [c.chunk['chunk_id'] for c in local_fused_limit(rows)]==[str(i) for i in range(16)]

def test_many_exact_hits_are_not_locally_cut_but_fused_hits_still_are():
    rows=[item('e'+str(i),0,exact=True,fused=False) for i in range(40)]+[item('f'+str(i),1/(i+1)) for i in range(20)]
    assert len(local_fused_limit(rows))==56

def test_fused_limits_are_independent_per_pack():
    rows=[item(str(i),1/(i+1),pack=pack) for pack in ['a','b'] for i in range(20)]
    assert len(local_fused_limit(rows))==32

def test_fused_ranking_does_not_use_exact_priority_tier():
    rows=[item('alias',.001,exact=True)]+[item(str(i),1/(i+1)) for i in range(20)]
    actual=local_fused_limit(rows)
    assert len(actual)==17 and [c.chunk['chunk_id'] for c in actual][1:]==[str(i) for i in range(16)]
