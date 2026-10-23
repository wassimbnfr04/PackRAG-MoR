"""Signed source field exposure; no authority resolution or legal-truth oracle."""
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from product.packrag.config import file_sha
from product.packrag.generator_api import Generated
from product.packrag.packs import SessionRegistry,VerifiedPack
from product.packrag.retrieval import Query,retrieve
from product.packrag.runtime import PackRAG
from product.packrag.source_metadata import source_metadata

ROOT=Path(__file__).resolve().parents[2]
CORPUS=ROOT/'artifacts/v1.3/m4/source-metadata-fixtures-0003'
REFERENCE=json.loads((CORPUS/'cases.json').read_text())


@pytest.fixture(scope='module')
def signed_pack():
    path=CORPUS/'source-metadata.kpack';assert file_sha(path)==REFERENCE['pack_sha256']
    with VerifiedPack(path,[(CORPUS/'public-key.raw').read_bytes()],developer_mode=True) as pack:yield pack


@pytest.mark.parametrize('case',REFERENCE['metadata_cases'],ids=lambda c:c['locator'])
def test_authenticated_nullable_source_values_and_bidirectional_edges(case,signed_pack):
    assert source_metadata(signed_pack,signed_pack.by_id[case['chunk_id']])==case['metadata']
    assert list(signed_pack.relations)==REFERENCE['relations']


@pytest.mark.parametrize('case',REFERENCE['retrieval_cases'],ids=lambda c:c['id'])
def test_metadata_neither_resolves_alias_ambiguity_nor_expands_graph(case,signed_pack):
    query=Query(REFERENCE['query_raw'],case['as_of'],case['jurisdiction'],case['current_law'])
    candidates,ambiguous=retrieve((signed_pack,),query,np.asarray(REFERENCE['query_vector'],dtype=np.float32))
    assert ambiguous==case['ambiguous']
    assert {c.chunk['locator'] for c in candidates}==set(case['expected_locators'])
    assert len(candidates)==len(case['candidates'])
    for actual,expected in zip(candidates,case['candidates'],strict=True):
        assert actual.chunk['chunk_id']==expected['chunk_id']
        assert (actual.sparse_rank,actual.dense_rank)==(expected['sparse_rank'],expected['dense_rank'])
        assert actual.rrf==expected['rrf']
        assert actual.dense_cosine==pytest.approx(expected['cosine'],abs=1e-7)


def test_exposed_metadata_does_not_mutate_verified_snapshot(signed_pack):
    case=next(c for c in REFERENCE['metadata_cases'] if c['locator']=='baseline')
    exposed=source_metadata(signed_pack,signed_pack.by_id[case['chunk_id']])
    exposed['relations'][0]['confidence']=42
    assert source_metadata(signed_pack,signed_pack.by_id[case['chunk_id']])==case['metadata']


def test_adjacent_cited_runtime_metadata_without_legal_ranking(signed_pack):
    class Generator:
        metadata={}
        def tokenize(self,text,*,add_special):return list(range(len(text.split())))
        def render_tokens(self,system,user):return self.tokenize(system+user,add_special=True)
        def generate(self,prompt):return Generated('hidden</think>74 °C. [S1]',False,(),{})
    registry=SessionRegistry();registry.activate(signed_pack)
    runtime=PackRAG(registry,SimpleNamespace(encode=lambda _:np.asarray(REFERENCE['query_vector'],dtype=np.float32)),Generator())
    result=runtime.answer(Query(REFERENCE['query_raw'],'2025-12-31','MA'))
    expected=next(c for c in REFERENCE['metadata_cases'] if c['locator']=='baseline')['metadata']
    assert result['state']=='ANSWER_ACCEPTED'
    assert result['sources'][0]['source_metadata']==result['selected'][0]['source_metadata']==result['candidates'][0]['source_metadata']==expected
    assert len(result['selected'])==1 and len(expected['relations'])==5  # Metadata edges do not add evidence.
