"""Fixed ownership/admission expectations; simulated mutations are not disk races."""
import copy
from dataclasses import FrozenInstanceError

import pytest

from product.packrag.config import PROFILE, RuntimeContractError
from product.packrag.evidence import own, export
from product.packrag.prompt import prepare, user_message
from product.packrag.retrieval import Query, retrieve
from product.tests.test_runtime_contracts import active, UnitEncoder, UnitTokenizer
from product.tests.test_conflict_integration import ControlledGenerator
from product.packrag.packs import SessionRegistry
from product.packrag.runtime import PackRAG
from types import SimpleNamespace


def test_nested_values_are_owned_and_cannot_be_written():
    source={'rows':[{'text':'original','pairs':[['a','b']]}]}
    frozen=own(source)
    source['rows'][0]['text']='changed';source['rows'][0]['pairs'][0][0]='changed'
    assert export(frozen)=={'rows':[{'text':'original','pairs':[['a','b']]}]}
    with pytest.raises(TypeError):frozen['rows'][0]['text']='changed'
    with pytest.raises(TypeError):frozen['rows'][0]['pairs'][0][0]='changed'
    exported=export(frozen);exported['rows'][0]['text']='changed'
    assert frozen['rows'][0]['text']=='original'


def test_prepared_canonical_metadata_origins_and_context_are_owned(active):
    pack,_=active;query=Query('Aster-9 temperature','2026-10-05')
    candidates,_=retrieve((pack,),query,UnitEncoder().encode('74'))
    prepared=prepare(query,(pack.identity,),candidates,UnitTokenizer())
    before=user_message(prepared.context.query,prepared.context.identities,list(prepared.evidence))
    rows=[copy.deepcopy(item.chunk) for item in candidates]
    manifest=copy.deepcopy(pack.manifest)
    try:
        for item in candidates:
            item.chunk['canonical_text']='changed';item.chunk['source_title']='changed';item.chunk['source_from']='2100-01-01'
        pack.manifest['version']='99.0.0';pack.manifest['publisher']['key_id']='changed'
        candidates.reverse();candidates.clear()
        assert user_message(prepared.context.query,prepared.context.identities,list(prepared.evidence))==before
        assert prepared.evidence[0].pack.identity[1]!='99.0.0'
        assert prepared.evidence[0].pack.manifest['publisher']['key_id']!='changed'
        assert prepared.evidence[0].origin_records[0].chunk['source_from'] is None
        assert prepared.context.query is not query
        with pytest.raises(TypeError):prepared.evidence[0].chunk['canonical_text']='changed'
        with pytest.raises(FrozenInstanceError):prepared.evidence[0].final_rank=99
        with pytest.raises(TypeError):prepared.context.profile['context_tokens']=9999
    finally:
        for original,row in zip(pack.chunks,rows,strict=True):original.clear();original.update(row)
        pack.manifest.clear();pack.manifest.update(manifest)


def test_freeze_precedes_tokenizer_callbacks(active):
    pack,_=active;query=Query('Aster-9 temperature','2026-10-05')
    candidates,_=retrieve((pack,),query,UnitEncoder().encode('74'))
    row=candidates[0].chunk;original=copy.deepcopy(row)
    class MutatingTokenizer(UnitTokenizer):
        metadata={'model_sha256':'original','nested':{'runtime':'original'}}
        def render_tokens(self,system,user):
            row['canonical_text']='callback changed';self.metadata['nested']['runtime']='changed'
            return super().render_tokens(system,user)
    tokenizer=MutatingTokenizer()
    try:
        prepared=prepare(query,(pack.identity,),candidates,tokenizer)
        assert prepared.evidence[0].chunk['canonical_text']==original['canonical_text']
        assert prepared.context.generator['nested']['runtime']=='original'
    finally:row.clear();row.update(original)


def test_candidate_pack_must_belong_to_frozen_active_identities(active):
    pack,_=active;query=Query('Aster-9','2026-10-05')
    candidates,_=retrieve((pack,),query,UnitEncoder().encode('74'))
    with pytest.raises(RuntimeContractError,match='ACTIVE_PACK_CHANGED'):
        prepare(query,(),candidates,UnitTokenizer())


def test_owned_profile_does_not_follow_mutable_global():
    snapshot=own(PROFILE)
    original=PROFILE['max_evidence_chunks']
    try:
        PROFILE['max_evidence_chunks']=99
        assert snapshot['max_evidence_chunks']==4
    finally:PROFILE['max_evidence_chunks']=original


@pytest.mark.parametrize('target,state',[
    ('version','ACTIVE_PACK_CHANGED'),('metadata','ACTIVE_PACK_CHANGED'),('canonical','EVIDENCE_CHANGED'),
    ('validity','EVIDENCE_CHANGED'),('profile','RUNTIME_PROFILE_CHANGED'),('generator','GENERATOR_IDENTITY_CHANGED')])
def test_final_admission_rejects_state_changed_during_budgeting(active,target,state):
    pack,_=active;registry=SessionRegistry();registry.activate(pack)
    original=copy.deepcopy(pack.manifest);profile=copy.deepcopy(PROFILE)
    original_rows=[copy.deepcopy(row) for row in pack.chunks]
    class Mutator(ControlledGenerator):
        def render_tokens(self,system,user):
            if target=='version':pack.manifest['version']='99.0.0'
            elif target=='metadata':pack.manifest['publisher']['key_id']='changed'
            elif target=='canonical':
                for row in pack.chunks:row['canonical_text']='changed'
            elif target=='validity':
                for row in pack.chunks:row['source_from']='2100-01-01'
            elif target=='profile':PROFILE['max_evidence_chunks']=99
            else:self.metadata={'changed':True}
            return super().render_tokens(system,user)
    generator=Mutator()
    try:
        result=PackRAG(registry,UnitEncoder(),generator).answer(Query('Aster-9','2026-10-05'))
        assert result['state']==state and generator.calls==0 and not result['selected']
    finally:
        pack.manifest.clear();pack.manifest.update(original);PROFILE.clear();PROFILE.update(profile)
        for row,old in zip(pack.chunks,original_rows,strict=True):row.clear();row.update(old)


def test_runtime_citations_remain_frozen_during_generation(active):
    pack,_=active;registry=SessionRegistry();registry.activate(pack)
    originals=[copy.deepcopy(row) for row in pack.chunks]
    class Mutator(ControlledGenerator):
        def generate(self,prompt):
            for row in pack.chunks:row['canonical_text']='post-admission mutation';row['locator']='changed'
            self.metadata={'changed':True}
            return super().generate(prompt)
    generator=Mutator();original_metadata=copy.deepcopy(generator.metadata)
    try:
        result=PackRAG(registry,UnitEncoder(),generator).answer(Query('Aster-9','2026-10-05'))
        assert result['state']=='ANSWER_ACCEPTED'
        assert result['sources'][0]['canonical_text']==originals[0]['canonical_text']
        assert result['sources'][0]['locator']==originals[0]['locator']
        assert result['generator']==result['evidence_context']['generator']==original_metadata
        assert result['selected'][0]['origin_records'][0]['chunk']['canonical_text']==originals[0]['canonical_text']
    finally:
        for row,original in zip(pack.chunks,originals,strict=True):row.clear();row.update(original)
