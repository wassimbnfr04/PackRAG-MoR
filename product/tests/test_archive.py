import json
from pathlib import Path
import pytest
from product.packrag.archive import audit_archive
from product.packrag.errors import PackError
from product.packrag.portable_names import fold
from product.packrag.packs import VerifiedPack

ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/"artifacts/v1.3/m3/archive-fixtures-0001"
CASES=json.loads((FOLDER/"cases.json").read_text(encoding="utf-8"))["cases"]

@pytest.mark.parametrize("case",CASES,ids=lambda c:c["id"])
def test_frozen_zip_audit_and_real_import(case):
    path=FOLDER/case["filename"]
    if case["audit_accept"]: audit_archive(path)
    else:
        with pytest.raises(PackError): audit_archive(path)
    public=(FOLDER/"public-key.raw").read_bytes()
    if case["accept"]:
        with VerifiedPack(path,[public],developer_mode=True) as pack: assert len(pack.chunks)==10
    else:
        with pytest.raises(PackError): VerifiedPack(path,[public],developer_mode=True)

def test_frozen_full_fold_contract():
    assert fold("ßςﬀİ") == "ssσffi\u0307"
    assert fold("ı") != fold("i")
    table=json.loads((ROOT/"product/config/portable-names.json").read_text())
    for code,mapped in table["mappings"].items(): assert fold(chr(int(code))) == mapped
