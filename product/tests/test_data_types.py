import json
from pathlib import Path
import pytest
from product.packrag import validation
from product.packrag.archive import safe_path, allowed_media_type
from product.packrag.config import file_sha
from product.packrag.errors import PackError
from product.packrag.packs import VerifiedPack

ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'artifacts/v1.3/m3/data-type-fixtures-0001'
CASES=[(folder,case) for folder in [FOLDER,ROOT/'artifacts/v1.3/m3/extension-name-fixtures-0001']
       for case in json.loads((folder/'cases.json').read_text())['cases']]

@pytest.mark.parametrize('folder,case',CASES,ids=[case['id'] for folder,case in CASES])
def test_signed_data_type_admission_before_payload_interpretation(folder,case,monkeypatch):
    calls=[]; original=validation.validate_database
    def database(*args,**kwargs):
        assert case['accept'], 'Forbidden type reached SQLite'
        calls.append(True); return original(*args,**kwargs)
    monkeypatch.setattr(validation,'validate_database',database)
    path=folder/case['filename']; assert file_sha(path)==case['sha256']
    if case['path_accept']: safe_path(case['path'])
    else:
        with pytest.raises(PackError): safe_path(case['path'])
    if case['accept']:
        allowed_media_type(case['path'],case['media_type'])
        with VerifiedPack(path,[(folder/'public-key.raw').read_bytes()],developer_mode=True) as pack:
            assert len(pack.chunks)==10
    else:
        with pytest.raises(PackError): allowed_media_type(case['path'],case['media_type'])
        with pytest.raises(PackError): VerifiedPack(path,[(folder/'public-key.raw').read_bytes()],developer_mode=True)
    assert bool(calls)==case['accept']; assert file_sha(path)==case['sha256']
