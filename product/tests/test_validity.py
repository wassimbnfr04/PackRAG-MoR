"""Independent interval expectations and authenticated adjacent retrieval tests."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from product.packrag.config import file_sha
from product.packrag.generator_api import Generated
from product.packrag.packs import SessionRegistry, VerifiedPack
from product.packrag.retrieval import Query, eligible, retrieve
from product.packrag.runtime import PackRAG
from product.packrag.validity import validity_provenance

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=json.loads((ROOT/'product/tests/validity-cases.json').read_text())
CORPUS=ROOT/'artifacts/v1.3/m4/validity-fixtures-0003'
REFERENCE=json.loads((CORPUS/'cases.json').read_text())


@pytest.mark.parametrize('case',CONTRACT['cases'],ids=lambda c:c['id'])
def test_fixed_interval_status_jurisdiction_contract(case):
    query=Query('question',case['as_of'],case['jurisdiction'],case['current_law'])
    assert eligible(case['row'],query)==case['eligible']


@pytest.mark.parametrize('case',CONTRACT['provenance_cases'],ids=lambda c:c['id'])
def test_fixed_original_effective_unknown_inherited_provenance(case):
    before=dict(case['row'])
    assert validity_provenance(case['row'])==case['expected']
    assert case['row']==before


@pytest.fixture(scope='module')
def signed_pack():
    path=CORPUS/'validity-boundaries.kpack';assert file_sha(path)==REFERENCE['pack_sha256']
    with VerifiedPack(path,[(CORPUS/'public-key.raw').read_bytes()],developer_mode=True) as pack:
        yield pack


@pytest.mark.parametrize('case',REFERENCE['cases'],ids=lambda c:c['id'])
def test_signed_validity_before_alias_sparse_dense_ranks(case,signed_pack):
    query=Query(REFERENCE['query_raw'],case['as_of'],case['jurisdiction'],case['current_law'])
    vector=np.asarray(REFERENCE['query_vector'],dtype=np.float32)
    candidates,ambiguous=retrieve((signed_pack,),query,vector)
    assert ambiguous==case['ambiguous']
    assert {c.chunk['locator'] for c in candidates}==set(case['expected_locators'])
    assert sorted(c.dense_rank for c in candidates)==list(range(1,len(candidates)+1))
    for actual,expected in zip(candidates,case['candidates'],strict=True):
        assert actual.chunk['chunk_id']==expected['chunk_id']
        assert actual.exact and actual.relevant
        assert (actual.sparse_rank,actual.dense_rank)==(expected['sparse_rank'],expected['dense_rank'])
        assert actual.rrf==expected['rrf']
        assert actual.dense_cosine==pytest.approx(expected['cosine'],abs=1e-7)
        assert validity_provenance(actual.chunk)==expected['validity']


def test_adjacent_runtime_cited_provenance_and_freshness_not_eligibility(signed_pack):
    # Controlled generator tests serialization, not model truth; real smoke required.
    class Generator:
        metadata={}
        def tokenize(self,text,*,add_special):return list(range(len(text.split())))
        def render_tokens(self,system,user):return self.tokenize(system+user,add_special=True)
        def generate(self,prompt):return Generated('hidden</think>74 °C. [S1]',False,(),{})
    registry=SessionRegistry();registry.activate(signed_pack)
    runtime=PackRAG(registry,SimpleNamespace(encode=lambda _:np.asarray(REFERENCE['query_vector'],dtype=np.float32)),Generator())
    result=runtime.answer(Query(REFERENCE['query_raw'],'2025-12-31','MA'))
    assert result['state']=='ANSWER_ACCEPTED'
    assert result['warnings']==[dict(pack_id=signed_pack.identity[0],reason='freshness_advisory')]
    expected=next(c for c in REFERENCE['cases'] if c['id']=='SOLE_BASELINE')['candidates'][0]['validity']
    assert result['sources'][0]['validity']==result['selected'][0]['validity']==result['candidates'][0]['validity']==expected
    assert result['sources'][0]['canonical_text']=='The synthetic Article-T temperature is 74 °C.'
    result=runtime.answer(Query(REFERENCE['query_raw'],'2030-01-01','MA'))
    assert result['state']=='NO_RELEVANT_EVIDENCE' and not result['selected']
