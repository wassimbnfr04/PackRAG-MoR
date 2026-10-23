import json
from pathlib import Path
import pytest
from kpack_builder.core import PackError
from product.packrag.config import file_sha
from product.packrag.packs import VerifiedPack
from product.packrag import validation
ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'artifacts/v1.3/m3/validation-order-fixtures-0001'

@pytest.mark.parametrize('case',json.loads((FOLDER/'cases.json').read_text())['cases'],ids=lambda c:c['id'])
def test_signed_phase_order_and_double_norm_boundaries(case,monkeypatch):
    calls=[]; original=validation.validate_database
    def database(*args,**kwargs):
        assert not case['before_db'],'Invalid KDX reached SQLite interpretation'
        calls.append(True); return original(*args,**kwargs)
    monkeypatch.setattr(validation,'validate_database',database)
    path=FOLDER/case['filename']; assert file_sha(path)==case['sha256']
    keys=[(FOLDER/'public-key.raw').read_bytes()]
    if case['accept']:
        with VerifiedPack(path,keys,developer_mode=True) as pack: assert len(pack.chunks)==10
    else:
        with pytest.raises(PackError,match=case['error_contains']): VerifiedPack(path,keys,developer_mode=True)
    assert bool(calls)!=case['before_db']
    assert file_sha(path)==case['sha256']
