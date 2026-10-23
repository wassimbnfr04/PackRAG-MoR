"""Signed global gate and controlled adjacent runtime; not actual LFM inference."""
import json
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from product.packrag.config import file_sha
from product.packrag.packs import VerifiedPack, SessionRegistry
from product.packrag.retrieval import Query, retrieve
from product.packrag.runtime import PackRAG
from product.tests.test_conflict_integration import ControlledGenerator

ROOT=Path(__file__).resolve().parents[2]
CORPUS=ROOT/'artifacts/v1.3/m4/relevance-fixtures-0001'
REFERENCE=json.loads((CORPUS/'cases.json').read_text())

@pytest.fixture(scope='module')
def packs():
    public=(CORPUS/'public-key.raw').read_bytes();assert file_sha(CORPUS/'public-key.raw')==REFERENCE['public_key_sha256']
    with ExitStack() as stack:
        values={}
        for record in REFERENCE['packs']:
            path=CORPUS/record['filename'];assert file_sha(path)==record['sha256']
            values[record['id']]=stack.enter_context(VerifiedPack(path,[public],developer_mode=True))
        yield values

@pytest.mark.parametrize('case',REFERENCE['cases'],ids=lambda c:c['id'])
def test_signed_global_relevance_and_runtime_pre_generation_guard(case,packs):
    query=Query(case['raw'],case['as_of']);vector=np.asarray(case['query_vector'],dtype=np.float32)
    active=tuple(packs[name] for name in case['packs']);actual,ambiguous=retrieve(active,query,vector)
    assert ambiguous==case['expected_ambiguous']
    assert [c.pack.identity[0].removeprefix('org.packrag.contract.') for c in actual]==case['expected_order']
    assert [c.relevant for c in actual]==case['expected_relevant']
    for item,row in zip(actual,case['candidates'],strict=True):
        assert item.chunk['chunk_id']==row['chunk_id'] and item.exact==row['exact']
        assert (item.sparse_rank,item.dense_rank,item.rrf)==(row['sparse_rank'],row['dense_rank'],row['rrf'])
        assert item.dense_cosine==pytest.approx(row['cosine'],abs=1e-7)
        assert [list(o) for o in item.origins]==row['origins']
    assert retrieve(tuple(reversed(active)),query,vector)==(actual,ambiguous)
    registry=SessionRegistry()
    for pack in active:registry.activate(pack)
    generator=ControlledGenerator();result=PackRAG(registry,SimpleNamespace(encode=lambda _:vector),generator).answer(query)
    assert result['state']==case['expected_state']
    if case['expected_state']=='NO_RELEVANT_EVIDENCE':
        assert generator.calls==0 and not result['selected'] and not result['sources'] and result['answer'] is None
    else:assert generator.calls==1 and '74 °C' in result['answer'] and result['sources']

def test_versioned_references_preserve_old_source_identities_and_shared_expectations():
    run=ROOT/'artifacts/v1.3/m4/relevance-references-0003'
    provenance=json.loads((run/'reference-provenance.json').read_text())
    for name,expected in provenance['history_sha256'].items():assert file_sha(ROOT/name)==expected
    assert [(r['kind'],r['id'],r['old_count'],r['new_count']) for r in provenance['changes']]==[
        ('query','AMBIGUITY_BEFORE_LOCAL_CAP',17,32),('conflict','BEFORE_CAP',16,32)]
    for name in ('query-reference.json','conflict-reference.json','reference-provenance.json'):
        assert (run/name).read_bytes()==(ROOT/'product/android/app/src/androidTest/assets/relevance-reference-corpus'/name).read_bytes()
    assert REFERENCE['fixed_gate_sha256']==file_sha(ROOT/'product/tests/fixtures/relevance-contracts.json')
    for name,field in [('fixed-expectations.json','fixed_expectations_sha256'),('embedding-inputs.json','embedding_inputs_sha256'),('source-specifications.json','source_specifications_sha256')]:
        assert file_sha(CORPUS/name)==REFERENCE[field]
