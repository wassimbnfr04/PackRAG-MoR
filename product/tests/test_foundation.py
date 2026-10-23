"""Foundation gates tie implementation configuration and coverage to the actual source."""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def test_every_normative_modal_and_schema_is_mapped():
    source=load('artifacts/v1.3/architecture/paragraphs.json')
    audit=load('artifacts/v1.3/architecture/requirements.json')
    mapped={r['paragraph'] for r in audit['requirements']}
    assert len(source)==audit['total_paragraphs']==1071
    explicit={p['index'] for p in source if re.search(r'\b(?:MUST(?: NOT)?|SHOULD(?: NOT)?|MAY)\b',p['text'])}
    assert explicit<=mapped
    assert {p['index'] for p in source if p['in_table']}<=mapped
    assert {p['index'] for p in source if 'CREATE TABLE' in p['text'] or 'CREATE VIRTUAL TABLE' in p['text']}<=mapped
    assert {246,280,532,540,546,548,633,639}<=mapped
    assert len({r['id'] for r in audit['requirements']})==len(audit['requirements'])
    assert all(r['status'] in {'NOT_STARTED','IMPLEMENTING','IMPLEMENTED','VERIFIED','BLOCKED','OPTIONAL_RESEARCH'} for r in audit['requirements'])

def test_lowercase_modal_and_rollback_policy_have_additive_source_bound_coverage():
    source=load('artifacts/v1.3/architecture/paragraphs.json')
    original=load('artifacts/v1.3/architecture/requirements.json')
    extra=load('docs/v1.3/supplemental-requirements.json')
    assert extra['architecture_sha256']==original['architecture_sha256']
    combined=original['requirements']+extra['requirements']
    assert len({r['id'] for r in combined})==len(combined)
    paragraphs={p['index']:p['text'] for p in source}
    assert all(paragraphs[r['paragraph']]==r['requirement'] for r in extra['requirements'])
    required={p['index'] for p in source if re.search(r'\b(?:must|should|may|forbidden|required|mandatory)\b',p['text'],re.I)}
    assert required<={r['paragraph'] for r in combined}
    assert 635 in {r['paragraph'] for r in extra['requirements']}


def test_frozen_product_profile_values():
    profile=load('product/config/runtime-profile.json')
    assert {k:profile[k] for k in ('sparse_candidate_k','dense_candidate_k','rrf_k','per_pack_fused_cap','cross_pack_pool_limit')} == {
        'sparse_candidate_k':24,'dense_candidate_k':24,'rrf_k':60,'per_pack_fused_cap':16,'cross_pack_pool_limit':32}
    assert (profile['context_tokens'],profile['prefill_tokens_cap'],profile['generated_tokens_cap'],profile['max_evidence_chunks'],profile['max_evidence_tokens_cap']) == (2048,1536,512,4,1200)
    assert profile['graph_enabled'] is False and profile['query_rewrite'] is False and profile['neural_reranker'] is False
    assert profile['temperature']==0 and profile['top_p']==1 and profile['batch_size']==1 and profile['product_language']=='en'
    assert profile['graph_benchmark']=={'profile_id':'mobile-v1-graph','seed_k':6,'max_extra':12,'max_hops':1}


def test_model_toolchain_pins_and_no_network_policy():
    lock=load('product/config/toolchain.lock.json')
    assert lock['generator']['sha256']=='a247afd6414918eac8e520a9e6137dc271235461ecbe1180462221d5b8d40b03'
    assert lock['generator']['llama_cpp_commit']=='19e28a27702117d8f2eb16b825b9a308111f67d9'
    assert lock['embedder']['revision']=='c61e626a6255c490879d0af885078b61929d51f6'
    assert lock['android']=={'jdk':'17','gradle':'9.6.0','agp':'9.4.0','kotlin':'2.4.20','ndk':'30.0.16248370','min_sdk':28,'compile_sdk':37,'target_sdk':37,'abi':'arm64-v8a','onnxruntime':'1.30.0','sqlite_bundled':'2.7.1','tink':'1.23.0','internet_permission':False}
    assert lock['generator']['public_weight_redistribution'] is False


def test_durable_plan_and_historical_separation():
    for name in ('PLAN.md','STATUS.md','DECISIONS.md','docs/architecture-compliance-matrix.md'):
        assert (ROOT/name).is_file()
    guard=load('artifacts/v1.3/m0/historical-evidence-guard.json')
    assert len(guard['files'])>=587
    assert guard['files']['FULL DOCUMENTATION.md']=='7c68e26003dc2debfbe4de9ce79467953fec5268c59947b93b2f2c01d612dbca'
    assert 'PROPOSED' in (ROOT/'docs/adr/0001-fallback-acceptance.md').read_text(encoding='utf-8')
    assert 'ACCEPTED' in (ROOT/'docs/adr/ADR-001-v13-lfm25-product-generator.md').read_text(encoding='utf-8')
