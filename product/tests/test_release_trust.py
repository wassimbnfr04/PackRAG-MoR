import json
from pathlib import Path
import pytest
from kpack_builder.core import PackError
from product.packrag.config import file_sha
from product.packrag.trust import load_trust, trusted_publishers
from product.packrag.packs import VerifiedPack
from product.packrag import validation

ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'artifacts/v1.3/m3/release-trust-fixtures-0001'
CORPUS=json.loads((FOLDER/'cases.json').read_text(encoding='utf-8'))
STORE_CASES=json.loads((FOLDER/'store-cases.json').read_text(encoding='utf-8'))

@pytest.mark.parametrize('case',STORE_CASES,ids=lambda c:c['id'])
def test_shared_approved_store_contract(case):
    if case['accept']:
        keys=trusted_publishers(case['value']); assert 1<=len(keys)<=8 and len(set(keys))==len(keys)
    else:
        with pytest.raises(PackError): trusted_publishers(case['value'])

@pytest.mark.parametrize('case',CORPUS['cases'],ids=lambda c:c['id'])
def test_production_admission_authentication_before_interpretation(case,monkeypatch):
    keys=load_trust(ROOT/'product/config/release-trust.json')
    path=FOLDER/case['filename']; assert file_sha(path)==case['sha256']
    def forbidden(*args,**kwargs): raise AssertionError('Rejected pack reached a later interpretation stage')
    if case['id']=='unknown-publisher': monkeypatch.setattr(validation,'bounded_structure',forbidden)
    if not case['accept_production']: monkeypatch.setattr(validation,'validate_database',forbidden)
    if case['accept_production']:
        with VerifiedPack(path,keys,developer_mode=False) as pack:
            assert len(pack.chunks)==10 and pack.vectors.shape==(10,384)
            assert pack.manifest['name']=='SYNTHETIC TRUST TEST — NOT RELEASE CALIBRATION'
    else:
        with pytest.raises(PackError,match=case['error_contains']): VerifiedPack(path,keys,developer_mode=False)
    assert file_sha(path)==case['sha256']

def test_actual_app_and_desktop_store_are_identical_and_development_signer_is_unknown():
    config=ROOT/'product/config/release-trust.json'
    assert config.read_bytes()==(ROOT/'product/android/app/src/main/assets/release-trust.json').read_bytes()
    assert file_sha(config)==CORPUS['approved_store_sha256']
    keys=load_trust(config); assert len(keys)==1
    with pytest.raises(PackError,match='Unknown signer or invalid signature'):
        VerifiedPack(ROOT/'artifacts/v1.3/m1/smoke-0001/developer-pack/walking-skeleton.kpack',keys,developer_mode=False)

@pytest.mark.parametrize('raw',[b'',b'\xff',b'{}'*32769,b'{"schema_version":"1.0","schema_version":"1.0"}',b'{',b'['*33+b']'*33],ids=['empty','invalid-utf8','oversize','duplicate-property','truncated-json','excess-depth'])
def test_raw_store_fails_closed(tmp_path,raw):
    path=tmp_path/'store.json'; path.write_bytes(raw)
    with pytest.raises((PackError,ValueError,UnicodeError)): load_trust(path)

def test_pretty_public_store_loads_without_requiring_pack_manifest_canonical_bytes():
    assert load_trust(ROOT/'product/config/release-trust.json')
