"""Independent original signed-row expectations; synthetic metadata is not genuine approval."""
import copy,json,hashlib
from pathlib import Path
import pytest
from product.packrag.packs import VerifiedPack
from product.packrag.source_attribution import source_attribution,source_location
from product.packrag.evidence import own,export,freeze_candidate
from product.packrag.retrieval import Query,retrieve
from product.packrag.config import RuntimeContractError
from product.tests.test_runtime_contracts import active,UnitEncoder

ROOT=Path(__file__).resolve().parents[2];ASSETS=ROOT/'product/android/app/src/androidTest/assets'
CORPUS=json.loads((ASSETS/'source-details-corpus/signed-row-expectations.json').read_text(encoding='utf-8'))

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def expected_attribution(row):
    return {key:(bool(row[key]) if key=='redistribution_allowed' else row[key]) for key in
        ['canonical_uri','retrieved_at','license','redistribution_allowed','source_type','snapshot_path','notes']}

@pytest.mark.parametrize('case',CORPUS['packs'],ids=lambda v:v['asset'])
def test_signed_original_source_rows_and_locations_survive_reader(case):
    path=ASSETS/case['asset'];public=ASSETS/case['public_key_asset']
    assert digest(path)==case['pack_sha256'] and digest(public)==case['public_key_sha256']
    with VerifiedPack(path,[public.read_bytes()],developer_mode=True) as pack:
        assert pack.identity==(case['pack_id'],case['version'],case['manifest_sha256'])
        assert [export(row) for row in pack.source_records]==case['sources']
        by_source={row['source_id']:row for row in case['sources']}
        by_chunk={row['chunk_id']:row for row in case['chunks']}
        for chunk in pack.chunks:
            expected=by_source[chunk['source_id']];original=by_chunk[chunk['chunk_id']]
            assert source_attribution(chunk)==expected_attribution(expected)
            assert source_location(chunk)==dict(chunk_title=original['title'],section=original['section'],
                page_start=original['page_start'],page_end=original['page_end'],character_start=original['character_start'],character_end=original['character_end'])
            assert chunk['canonical_text']==original['canonical_text'] and chunk['text_sha256']==original['text_sha256']
            if expected['snapshot_path']:
                assert digest(pack.root/expected['snapshot_path'])==expected['sha256_original']
        captured=pack.source_records
        with pytest.raises(TypeError):captured[0]['license']='changed'
    assert [export(row) for row in captured]==case['sources']

def test_orphan_false_redistribution_and_snapshot_are_independent():
    case=CORPUS['packs'][-1]
    assert len(case['sources'])==11 and len(case['chunks'])==10
    orphan=next(r for r in case['sources'] if r['source_id']=='dev-unused')
    assert not any(r['source_id']=='dev-unused' for r in case['chunks'])
    assert source_attribution(orphan)['redistribution_allowed'] is False
    assert orphan['canonical_uri'] is None and orphan['snapshot_path'] is None
    snapshot=next(r for r in case['sources'] if r['snapshot_path'])
    assert snapshot['canonical_uri']=='https://example.invalid/synthetic/thermal' and snapshot['license']=='CC0-1.0'

@pytest.mark.parametrize('invalid',[2,-1,'1',1.5])
def test_invalid_redistribution_value_is_not_silently_coerced(invalid):
    with pytest.raises(RuntimeContractError,match='INVALID_SOURCE_ATTRIBUTION'):source_attribution({'redistribution_allowed':invalid})

def test_missing_attribution_is_explicit_unknown_not_false_or_empty():
    assert source_attribution({})=={key:None for key in ['canonical_uri','retrieved_at','license','redistribution_allowed','source_type','snapshot_path','notes']}

def test_selected_and_each_origin_own_attribution_after_live_mutation_and_close(active):
    pack,_=active;query=Query('Aster-9 temperature','2026-10-05')
    candidates,_=retrieve((pack,),query,UnitEncoder().encode('74'));candidate=candidates[0]
    original=copy.deepcopy(candidate.chunk);frozen=freeze_candidate(candidate);expected=source_attribution(frozen.chunk)
    try:
        candidate.chunk.update(license='CHANGED',retrieved_at='2100-01-01',redistribution_allowed=0,notes='CHANGED')
        assert source_attribution(frozen.chunk)==expected
        assert source_attribution(frozen.origin_records[0].chunk)==expected
        record=frozen.origin_records[0].record();record['source_attribution']['license']='EXPORTED_CHANGE'
        assert frozen.origin_records[0].record()['source_attribution']==expected
        with pytest.raises(TypeError):frozen.chunk['license']='CHANGE'
    finally:candidate.chunk.clear();candidate.chunk.update(original)
