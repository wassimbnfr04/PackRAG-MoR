"""Signed retrieval/admission integration; controlled generator is not LFM inference."""
import json
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from product.packrag.config import RuntimeContractError, file_sha
from product.packrag.generator_api import Generated
from product.packrag.packs import VerifiedPack, SessionRegistry
from product.packrag.prompt import prepare
from product.packrag.retrieval import Query, retrieve, retrieve_pack
from product.packrag.runtime import PackRAG

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "artifacts/v1.3/m4/conflict-fixtures-0001"
REFERENCE = json.loads((ROOT / "artifacts/v1.3/m4/relevance-references-0003/conflict-reference.json").read_text())


@pytest.fixture(scope="module")
def packs():
    with ExitStack() as stack:
        public=[]
        for record in REFERENCE["public_keys"]:
            path=CORPUS/record["filename"];assert file_sha(path)==record["sha256"];public.append(path.read_bytes())
        values={}
        for record in REFERENCE["packs"]:
            path=CORPUS/record["filename"];assert file_sha(path)==record["sha256"]
            values[record["id"]]=stack.enter_context(VerifiedPack(path,public,developer_mode=True))
        yield values


@pytest.mark.parametrize("case", REFERENCE["cases"], ids=lambda case: case["id"])
def test_signed_conflict_sets_ranks_provenance_and_caller_order(case,packs):
    query=Query(case["raw"],case["as_of"],case["jurisdiction"],case["current_law"])
    vector=np.asarray(case["query_vector"],dtype=np.float32);active=tuple(packs[name] for name in case["packs"])
    actual,ambiguous=retrieve(active,query,vector)
    assert ambiguous==case["expected_ambiguous"] and len(actual)==len(case["candidates"])
    if case["expected_locators"] is not None:
        assert {c.pack.identity[0].split('.')[-1]+"/"+c.chunk["locator"] for c in actual}==set(case["expected_locators"])
    base={c.origin_key:c for pack in active for c in retrieve_pack(pack,query,vector,limit=False)[0]}
    for item,row in zip(actual,case["candidates"],strict=True):
        assert (item.pack.identity[0],item.chunk['chunk_id'])==(row['pack_id'],row['chunk_id'])
        assert (item.exact,item.relevant,item.sparse_rank,item.dense_rank,item.rrf)==(row['exact'],row['relevant'],row['sparse_rank'],row['dense_rank'],row['rrf'])
        assert item.dense_cosine==pytest.approx(row['cosine'],abs=1e-7)
        assert [list(origin) for origin in item.origins]==row['origins']
        assert json.loads(json.dumps([asdict(d) for d in item.conflicts]))==row['conflicts']
        unchanged=base[item.origin_key]
        assert (item.sparse_rank,item.dense_rank,item.rrf,item.dense_cosine)==(unchanged.sparse_rank,unchanged.dense_rank,unchanged.rrf,unchanged.dense_cosine)
    reverse,reverse_ambiguity=retrieve(tuple(reversed(active)),query,vector)
    assert reverse==actual and reverse_ambiguity==ambiguous
    if case['id'] in ('UNRELATED','ARTICLES'):
        assert not any(item.conflicts for item in actual)
        assert actual==sorted(actual,key=lambda item:item.key)


class ControlledGenerator:
    metadata={"purpose":"CONTROLLED_PROTOCOL_NOT_LFM_INFERENCE"}
    def __init__(self):self.calls=0
    def tokenize(self,text,*,add_special=False):return list(range(len(text.split())))
    def render_tokens(self,system,user):return self.tokenize(system+user)
    def generate(self,prompt):
        self.calls+=1
        return Generated("hidden</think>74 °C. "+''.join(f'[S{i}]' for i in range(1,len(prompt.evidence)+1)),False,(),{})


@pytest.mark.parametrize('identity',['UNKNOWN','WEAK','CYCLE','UNRELATED','ARTICLES','DIFFERENT_CURATORS','BEFORE_CAP','FIVE_COMPANIONS','AUTHORITY','AMENDS','EXCEPTION'])
def test_runtime_stops_before_generation_or_preserves_required_canonical_sources(identity,packs):
    case=next(row for row in REFERENCE['cases'] if row['id']==identity)
    registry=SessionRegistry()
    for name in case['packs']:registry.activate(packs[name])
    generator=ControlledGenerator();vector=np.asarray(case['query_vector'],dtype=np.float32)
    runtime=PackRAG(registry,SimpleNamespace(encode=lambda _:vector),generator)
    result=runtime.answer(Query(case['raw'],case['as_of'],case['jurisdiction']))
    if case['expected_ambiguous']:
        assert result['state']=='IDENTIFIER_AMBIGUOUS' and generator.calls==0 and not result['selected']
    elif identity=='FIVE_COMPANIONS':
        assert result['state']=='INCOMPLETE_LEGAL_CONFLICT_EVIDENCE' and generator.calls==0
    else:
        assert result['state']=='ANSWER_ACCEPTED' and generator.calls==1
        assert len(result['sources'])==len(case['expected_locators'])
        assert all(source['conflicts'] for source in result['sources'])
        assert any('74 °C' in source['canonical_text'] for source in result['sources'])


def test_unresolved_selected_conflict_rejects_even_when_called_without_alias_gate(packs):
    case=next(row for row in REFERENCE['cases'] if row['id']=='UNKNOWN')
    query=Query(case['raw'],case['as_of'],case['jurisdiction']);pack=packs['unknown']
    candidates,_=retrieve((pack,),query,np.asarray(case['query_vector'],dtype=np.float32))
    with pytest.raises(RuntimeContractError,match='LEGAL_CONFLICT_UNRESOLVED'):
        prepare(query,(pack.identity,),candidates,ControlledGenerator())
