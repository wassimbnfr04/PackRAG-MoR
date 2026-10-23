"""Signed pool/ownership controls, controlled counts separate from actual GGUF refs."""
from contextlib import ExitStack
from dataclasses import asdict
import json
from pathlib import Path
import numpy as np
import pytest

from product.packrag.config import file_sha, RuntimeContractError
from product.packrag.packs import VerifiedPack
from product.packrag.prompt import prepare
from product.packrag.retrieval import Query, retrieve
from product.tests.test_conflict_integration import ControlledGenerator

ROOT=Path(__file__).resolve().parents[2]
CORPUS=ROOT/'artifacts/v1.3/m4/selection-fixtures-0002'
REFERENCE=json.loads((CORPUS/'cases.json').read_text())


@pytest.fixture(scope='module')
def packs():
    public=(CORPUS/'public-key.raw').read_bytes();assert file_sha(CORPUS/'public-key.raw')==REFERENCE['public_key_sha256']
    with ExitStack() as stack:
        yield {row['id']:stack.enter_context(VerifiedPack(CORPUS/row['filename'],[public],developer_mode=True)) for row in REFERENCE['packs']}


@pytest.mark.parametrize('case',REFERENCE['cases'],ids=lambda row:row['id'])
def test_signed_pool_positions_and_complete_actual_origin_context(case,packs):
    pack=packs[case['id']];query=Query(case['raw'],case['as_of'],case['jurisdiction'])
    actual,ambiguous=retrieve((pack,),query,np.asarray(case['query_vector'],dtype=np.float32))
    assert not ambiguous and [item.chunk['chunk_id'] for item in actual]==case['expected_pool']
    assert [item.final_rank for item in actual]==list(range(1,len(actual)+1))
    for item in actual:
        origin=item.origin_records[0]
        assert origin.identity==pack.identity and dict(origin.chunk)==item.chunk
        assert (origin.exact,origin.sparse_rank,origin.dense_rank,origin.cosine,origin.rrf)==(
            item.exact,item.sparse_rank,item.dense_rank,item.dense_cosine,item.rrf)
    if case['id'].startswith('boundary'):
        # Synthetic split counts cannot validate exact actual-GGUF boundaries.
        return
    if case['expected_admission']=='READY':
        prompt=prepare(query,(pack.identity,),actual,ControlledGenerator())
        assert [item.chunk['chunk_id'] for item in prompt.evidence]==case['expected_selected']
        reversed_prompt=prepare(query,(pack.identity,),list(reversed(actual)),ControlledGenerator())
        assert prompt.tokens==reversed_prompt.tokens and prompt.selection==reversed_prompt.selection
        assert prompt.evidence[0].final_rank==1 and prompt.evidence[-1].final_rank==5
    else:
        with pytest.raises(RuntimeContractError,match='^'+case['expected_admission']+'$') as caught:
            prepare(query,(pack.identity,),actual,ControlledGenerator())
        assert caught.value.selection.admission==case['expected_admission'] and not caught.value.selection.keys


def test_signed_fixture_shared_bytes_and_independent_oracles_are_bound():
    for key,name in [('script_sha256','scripts/v13_selection_fixtures.py'),('builder_sha256','scripts/v13_query_identifier_fixtures.py'),
                     ('fixed_contract_sha256','product/tests/fixtures/selection-contracts.json')]:assert file_sha(ROOT/name)==REFERENCE[key]
    for key,name in [('fixed_expectations_sha256','fixed-expectations.json'),('independent_ranks_sha256','independent-ranks.json'),
                     ('embedding_inputs_sha256','embedding-inputs.json')]:assert file_sha(CORPUS/name)==REFERENCE[key]
    assets=ROOT/'product/android/app/src/androidTest/assets/selection-corpus'
    assert (assets/'cases.json').read_bytes()==(CORPUS/'cases.json').read_bytes()
    assert (assets/'selection-contracts.json').read_bytes()==(ROOT/'product/tests/fixtures/selection-contracts.json').read_bytes()
    for row in REFERENCE['packs']:assert file_sha(assets/row['filename'])==file_sha(CORPUS/row['filename'])==row['sha256']
    boundary=next(case for case in REFERENCE['cases'] if case['id']=='boundary1200')
    assert boundary['actual_tokenizer']['evidence_tokens']==1200 and boundary['actual_tokenizer']['prefill_tokens']<=1536


def test_literal_dedup_preserves_distinct_local_chunk_origins_within_one_pack():
    corpus=ROOT/'artifacts/v1.3/m4/query-identifier-fixtures-0001'
    reference=json.loads((corpus/'cases.json').read_text())
    case=next(row for row in reference['cases'] if row['id']=='WITHIN_PACK_DEDUP_ORIGIN_UNIQUE')
    record=next(row for row in reference['packs'] if row['id']=='within-duplicate')
    with VerifiedPack(corpus/record['filename'],[(corpus/'public-key.raw').read_bytes()],developer_mode=True) as pack:
        values,_=retrieve((pack,),Query(case['raw'],case['as_of']),np.asarray(case['query_vector'],dtype=np.float32))
        assert len(values)==1 and len(values[0].origins)==1 and len(values[0].origin_records)==2
        assert {v.chunk['chunk_id'] for v in values[0].origin_records}=={row['chunk_id'] for row in pack.chunks}
        assert {v.chunk['locator'] for v in values[0].origin_records}=={'first','second'}
