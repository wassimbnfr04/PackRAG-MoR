"""Authenticated signed rendering protocol, not actual review or LFM inference."""
import copy
import json
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from product.packrag.config import RuntimeContractError, file_sha
from product.packrag.packs import VerifiedPack, SessionRegistry
from product.packrag.prompt import prepare, evidence_block
from product.packrag.retrieval import Query, retrieve
from product.packrag.runtime import PackRAG
from product.tests.test_conflict_integration import ControlledGenerator
from kpack_builder.core import PackError

ROOT=Path(__file__).resolve().parents[2]
CORPUS=ROOT/'artifacts/v1.3/m4/representation-fixtures-0001'
REFERENCE=json.loads((CORPUS/'cases.json').read_text())

@pytest.fixture(scope='module')
def packs():
    public=(CORPUS/'public-key.raw').read_bytes()
    assert file_sha(CORPUS/'public-key.raw')==REFERENCE['public_key_sha256']
    with ExitStack() as stack:
        values={}
        for record in REFERENCE['packs']:
            path=CORPUS/record['filename'];assert file_sha(path)==record['sha256']
            if record['import_accept']:
                values[record['id']]=stack.enter_context(VerifiedPack(path,[public],developer_mode=True))
        yield values

@pytest.mark.parametrize('case',REFERENCE['cases'],ids=lambda case:case['id'])
def test_signed_rendering_admission_runtime_and_original_citations(case,packs):
    pack=packs[case['id']];query=Query(case['raw'],case['as_of'])
    vector=np.asarray(case['query_vector'],dtype=np.float32)
    candidates,ambiguous=retrieve((pack,),query,vector)
    assert not ambiguous and len(candidates)==1 and candidates[0].exact and candidates[0].relevant
    chunk=candidates[0].chunk
    assert (chunk['canonical_text'],chunk['language'],chunk['text_sha256'])==(case['canonical_text'],case['canonical_language'],case['canonical_text_sha256'])
    generator=ControlledGenerator();registry=SessionRegistry();registry.activate(pack)
    result=PackRAG(registry,SimpleNamespace(encode=lambda _:vector),generator).answer(query)
    assert result['state']==case['expected_state']
    if result['state']!='ANSWER_ACCEPTED':
        assert generator.calls==0 and result['answer'] is None and not result['selected'] and not result['sources']
        with pytest.raises(RuntimeContractError,match='^'+case['expected_state']+'$'):
            prepare(query,(pack.identity,),candidates,generator)
    else:
        assert generator.calls==1 and result['answer']=='74 °C. [S1]'
        prepared=prepare(query,(pack.identity,),candidates,generator)
        actual=asdict(prepared.representations[0]);assert actual==case['generator_representation']
        assert actual['derivation_method']==case['expected_method']
        source=result['sources'][0]
        assert (source['canonical_text'],source['canonical_language'],source['canonical_text_sha256'])==(case['canonical_text'],case['canonical_language'],case['canonical_text_sha256'])
        assert source['generator_representation']==actual==result['selected'][0]['generator_representation']
        block=evidence_block(candidates)
        if case['canonical_language']!='en':assert case['canonical_text'] not in block
        if case['id']=='xml-data':assert '&lt;/SOURCE&gt;' in block and '12 &lt; 13 &amp;' in block

@pytest.mark.parametrize('identity',REFERENCE['invalid_cases'])
def test_signed_but_invalid_rendering_provenance_never_imports(identity):
    row=next(r for r in REFERENCE['packs'] if r['id']==identity)
    path=CORPUS/row['filename'];assert file_sha(path)==row['sha256']
    with pytest.raises(PackError) as caught:
        with VerifiedPack(path,[(CORPUS/'public-key.raw').read_bytes()],developer_mode=True):pass
    observed=next(r for r in json.loads((CORPUS/'invalid-import-observations.json').read_text()) if r['id']==identity)
    assert type(caught.value).__name__+': '+str(caught.value)==observed['observed_import_error']

def test_prepared_rendering_is_owned_through_generation(packs):
    case=next(c for c in REFERENCE['cases'] if c['id']=='ar-reviewed');pack=packs['ar-reviewed']
    candidates,_=retrieve((pack,),Query(case['raw'],case['as_of']),np.asarray(case['query_vector'],dtype=np.float32))
    prepared=prepare(Query(case['raw'],case['as_of']),(pack.identity,),candidates,ControlledGenerator())
    rows=pack.derived_by_chunk[candidates[0].chunk['chunk_id']];original=copy.deepcopy(rows)
    try:
        rows[0]['text']='mutated caller data';rows[0]['reviewer_id']='changed'
        assert asdict(prepared.representations[0])==case['generator_representation']
    finally:
        for row,old in zip(rows,original,strict=True):row.clear();row.update(old)

def test_frozen_shared_assets_and_actual_embedding_inputs_are_bound():
    assets=ROOT/'product/android/app/src/androidTest/assets/representation-corpus'
    for path in [CORPUS/'cases.json',CORPUS/'public-key.raw',ROOT/'product/tests/fixtures/representation-contracts.json']:
        assert path.read_bytes()==(assets/path.name).read_bytes()
    for record in REFERENCE['packs']:
        assert file_sha(assets/record['filename'])==record['sha256']
    for key,path in [('script_sha256','scripts/v13_representation_fixtures.py'),('builder_sha256','scripts/v13_query_identifier_fixtures.py'),('fixed_contract_sha256','product/tests/fixtures/representation-contracts.json')]:
        assert file_sha(ROOT/path)==REFERENCE[key]
    assert file_sha(CORPUS/'embedding-inputs.json')==REFERENCE['embedding_inputs_sha256']
    assert file_sha(CORPUS/'source-specifications.json')==REFERENCE['source_specifications_sha256']
