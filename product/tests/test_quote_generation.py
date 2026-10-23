"""Synthetic adjacent checks; actual LFM/device acceptance is separately recorded."""
from dataclasses import FrozenInstanceError
import pytest
from product.packrag.config import PROFILE, RuntimeContractError
from product.packrag.generation_policy import BASELINE, QUOTES, quote_units, quote_grammar, matches_quote_units
from product.packrag.generator_api import Generated
from product.packrag.packs import SessionRegistry
from product.packrag.runtime import PackRAG
from product.packrag.retrieval import Query
from product.tests.test_runtime_contracts import active, UnitEncoder, UnitTokenizer


def test_baseline_and_revision_do_not_mutate_retrieval_or_each_other():
    before=dict(PROFILE)
    revision=QUOTES.runtime_profile(PROFILE)
    assert (revision['context_tokens'],revision['generated_tokens_cap'])==(3072,1536)
    assert revision['compatible_retrieval_profile']=='mobile-v1'
    assert BASELINE.runtime_profile(PROFILE)==before==PROFILE
    assert (PROFILE['context_tokens'],PROFILE['generated_tokens_cap'])==(2048,512)
    with pytest.raises(FrozenInstanceError): QUOTES.generated=99


@pytest.mark.parametrize('final,expected',[
    ('1. Disconnect power. [S1]',True),
    ('1. Disconnect power. [S1]\n2. Débrancher l’alimentation. [S2]',True),
    ('1. Connect power. [S1]',False),
    ('1. Disconnect power. [S9]',False),
    ('Disconnect power. [S1]',False),
    ('2. Disconnect power. [S1]',False),
    ('1. Disconnect power. [S1]\n2. Disconnect power. [S1]',False),
])
def test_independent_admission_rejects_invented_text_wrong_identity_and_duplicate_units(final,expected):
    units=quote_units(['Disconnect power.','Débrancher l’alimentation.'])
    assert matches_quote_units(final,units) is expected


def test_unicode_physical_line_units_and_literal_escape_are_owned_and_bounded():
    texts=['  تأكد من فصل الطاقة.\r\nDébrancher "A\\B".\u2028Final check.','Second source.']
    units=quote_units(texts);texts.clear()
    assert units==('تأكد من فصل الطاقة. [S1]','Débrancher "A\\B". [S1]','Final check. [S1]','Second source. [S2]')
    grammar=quote_grammar(units)
    assert '\\"A\\\\B\\"' in grammar and '[S9]' not in grammar
    with pytest.raises(RuntimeContractError): quote_units(['\n\n'])
    with pytest.raises(RuntimeContractError): quote_units(['x']*5)
    with pytest.raises(RuntimeContractError): quote_units(['\n'.join(str(i) for i in range(65))])


@pytest.mark.parametrize('payload,truncated,state',[
    ('outside',False,'OUTPUT_REJECTED'),
    ('exact',False,'ANSWER_ACCEPTED'),
    ('exact',True,'GENERATION_UNUSABLE'),
])
def test_actual_adjacent_runtime_rechecks_source_units_even_if_backend_ignores_grammar(active,payload,truncated,state):
    pack,_=active
    class Backend(UnitTokenizer):
        metadata={'test':'synthetic-no-weight-inference'}
        generation_policy=QUOTES
        def generate(self,prompt):
            assert prompt.generation_policy==QUOTES
            assert prompt.context.profile['profile_id']==QUOTES.profile_id
            assert prompt.max_new_tokens<=1536
            units=quote_units(row.text for row in prompt.representations)
            final='1. '+units[0] if payload=='exact' else '1. Invented 200 °C. [S1]'
            return Generated('PRIVATE_IN_MEMORY</think>'+final,truncated,(1,2),{})
    registry=SessionRegistry();registry.activate(pack)
    result=PackRAG(registry,UnitEncoder(),Backend(),QUOTES).answer(Query('Aster-9 temperature','2026-10-05'))
    assert result['state']==state
    if state!='ANSWER_ACCEPTED':assert result['answer'] is None and result['sources']==[]
    assert 'PRIVATE_IN_MEMORY' not in str(result)


def test_generation_callback_cannot_disable_the_captured_quotation_gate(active):
    pack,_=active
    class Backend(UnitTokenizer):
        metadata={'test':'synthetic-policy-mutation'}
        generation_policy=QUOTES
        def generate(self,prompt):
            runtime.generation_policy=BASELINE
            return Generated('private</think>1. Invented 200 °C. [S1]',False,(1,2),{})
    registry=SessionRegistry();registry.activate(pack)
    runtime=PackRAG(registry,UnitEncoder(),Backend(),QUOTES)
    result=runtime.answer(Query('Aster-9 temperature','2026-10-05'))
    assert result['state']=='OUTPUT_REJECTED' and result['answer'] is None and result['sources']==[]
