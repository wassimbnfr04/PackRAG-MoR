import json
from pathlib import Path
import pytest
from product.packrag.packs import VerifiedPack
from product.packrag.config import file_sha
from product.packrag.manifest import compare_versions

ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/"artifacts/v1.3/m3/lifecycle-fixtures-0001"
CASES=json.loads((FOLDER/"cases.json").read_text())["cases"]

@pytest.mark.parametrize("case",CASES,ids=lambda c:c["id"])
def test_independent_desktop_validation_of_lifecycle_inputs(case):
    path=FOLDER/case["filename"]; assert file_sha(path)==case["sha256"]
    with VerifiedPack(path,[(FOLDER/"public-key.raw").read_bytes()],developer_mode=True) as pack:
        assert pack.identity[1:]==(case["version"],case["manifest_sha256"])
        assert len(pack.chunks)==10

def test_lifecycle_fixture_identities_and_order():
    records={c["id"]:c for c in CASES}
    assert records["v2"]["manifest_sha256"]!=records["collision"]["manifest_sha256"]
    assert records["v2"]["version"]==records["collision"]["version"]
    assert compare_versions(records["v3"]["version"],records["v2"]["version"])>0
    assert compare_versions(records["equal-build"]["version"],records["v2"]["version"])==0

def test_valid_zero_row_kdx_and_database_mount():
    folder=ROOT/"artifacts/v1.3/m3/empty-fixture-0001"
    case=json.loads((folder/"case.json").read_text())
    with VerifiedPack(folder/"empty.kpack",[(folder/"public-key.raw").read_bytes()],developer_mode=True) as pack:
        assert pack.identity[2]==case["manifest_sha256"]
        assert pack.chunks==() and pack.vectors.shape==(0,384)
        assert not pack.db.execute("SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ?",('"Aster"',)).fetchall()
