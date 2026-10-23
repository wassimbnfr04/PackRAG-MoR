"""Independent presence/scalar/provenance and signed NEL regressions."""
import hashlib,json
from pathlib import Path
import pytest
from kpack_builder.core import PackError
from product.packrag.config import RuntimeContractError,file_sha
from product.packrag.packs import VerifiedPack
from product.packrag.representations import nonblank,select_representation
ROOT=Path(__file__).resolve().parents[2]
FIXED=json.loads((ROOT/'product/tests/fixtures/source-text-contracts.json').read_text())
CORPUS=ROOT/'artifacts/v1.3/m4/source-text-fixtures-0001'
REFERENCE=json.loads((CORPUS/'cases.json').read_text())
digest=lambda text:hashlib.sha256(text.encode()).hexdigest()

@pytest.mark.parametrize('case',FIXED['cases'],ids=lambda c:c['id'])
def test_independently_fixed_presence(case):assert nonblank(case['value'])==case['expected_nonblank']

def test_pinned_python_presence_for_every_valid_unicode_scalar():
    whitespace=set(FIXED['whitespace_points']);count=0
    for point in range(0x110000):
        if 0xd800<=point<=0xdfff:continue
        assert nonblank(chr(point))==(point not in whitespace);count+=1
    assert count==1112064

@pytest.mark.parametrize('point',FIXED['whitespace_points'])
@pytest.mark.parametrize('field',['canonical','text','derivation_source','reviewer_id'])
def test_every_blank_scalar_fails_resolver_provenance(field,point):
    canonical=dict(canonical_text='Source.',text_sha256=digest('Source.'),language='en' if field=='canonical' else 'fr')
    row=dict(purpose='generator',language='en',text='74 °C.',text_sha256=digest('74 °C.'),derivation_method='human_reviewed_translation',derivation_source='SYNTHETIC',reviewer_id='SYNTHETIC',reviewed_at='2026-10-09')
    if field=='canonical':canonical.update(canonical_text=chr(point),text_sha256=digest(chr(point)))
    else:
        row[field]=chr(point)
        if field=='text':row['text_sha256']=digest(chr(point))
    with pytest.raises(RuntimeContractError,match='^INVALID_GENERATOR_PROVENANCE$'):select_representation(canonical,[row])

@pytest.mark.parametrize('record',REFERENCE['packs'],ids=lambda r:r['id'])
def test_signed_nel_fields_reject_or_preserve_original_bytes(record):
    path=CORPUS/record['filename'];assert file_sha(path)==record['sha256'];public=(CORPUS/'public-key.raw').read_bytes()
    if not record['accept']:
        with pytest.raises(PackError) as caught:VerifiedPack(path,[public],developer_mode=True)
        assert type(caught.value).__name__+': '+str(caught.value)==record['observed_import_error']
    else:
        with VerifiedPack(path,[public],developer_mode=True) as pack:
            chunk=pack.chunks[0];rendering=select_representation(chunk,pack.derived_by_chunk[chunk['chunk_id']])
            assert rendering.__dict__==record['generator_representation'] and chunk['canonical_text']==record['canonical_text']
            assert rendering.derivation_source==record['expected_derived']['derivation_source'] and rendering.reviewer_id==record['expected_derived']['reviewer_id']

def test_frozen_signed_presence_inputs_and_shared_assets():
    assets=ROOT/'product/android/app/src/androidTest/assets/source-text-corpus'
    for path in [CORPUS/'cases.json',CORPUS/'public-key.raw',ROOT/'product/tests/fixtures/source-text-contracts.json',*[CORPUS/r['filename'] for r in REFERENCE['packs']]]:
        assert path.read_bytes()==(assets/path.name).read_bytes()
    for path,key in [('scripts/v13_source_text_fixtures.py','script_sha256'),('scripts/v13_query_identifier_fixtures.py','builder_sha256'),('scripts/v13_representation_fixtures.py','rendering_helper_sha256'),('product/tests/fixtures/source-text-contracts.json','fixed_contract_sha256')]:assert file_sha(ROOT/path)==REFERENCE[key]
    for filename,key in [('public-key.raw','public_key_sha256'),('source-specifications.json','source_specifications_sha256'),('embedding-inputs.json','embedding_inputs_sha256')]:assert file_sha(CORPUS/filename)==REFERENCE[key]
