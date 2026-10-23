import json
from pathlib import Path
import pytest
from kpack_builder.core import PackError
from product.packrag.packs import VerifiedPack
from product.packrag.languages import valid_tag
from product.packrag.normalization import normalize
from product.packrag.temporal import iso_date, utc_timestamp
from product.packrag.database import normalized_sql

ROOT=Path(__file__).resolve().parents[2]
CASES=json.loads(Path(__file__).with_name("database-cases.json").read_text())
FORMATS=json.loads(Path(__file__).with_name("format-cases.json").read_text())

@pytest.mark.parametrize("case",CASES,ids=lambda c:c["id"])
def test_signed_hostile_db_corpus(case):
    folder=ROOT/"artifacts/v1.3/m3/database-fixtures-0001"
    public=(folder/"public-key.raw").read_bytes(); path=folder/(case["id"]+".kpack")
    if case["accept"]:
        with VerifiedPack(path,[public],developer_mode=case.get("developer_mode",True)) as pack: assert len(pack.chunks)==10
    else:
        with pytest.raises(PackError): VerifiedPack(path,[public],developer_mode=case.get("developer_mode",True))

@pytest.mark.parametrize("value,expected",FORMATS["languages"])
def test_language_syntax(value,expected): assert valid_tag(value)==expected

@pytest.mark.parametrize("value,expected",FORMATS["dates"])
def test_dates(value,expected):
    if expected: iso_date(value)
    else:
        with pytest.raises(ValueError): iso_date(value)

@pytest.mark.parametrize("value,expected",FORMATS["timestamps"])
def test_utc(value,expected):
    if expected: utc_timestamp(value)
    else:
        with pytest.raises(ValueError): utc_timestamp(value)

@pytest.mark.parametrize("value,expected",FORMATS["normalization"])
def test_normalization_contract(value,expected): assert normalize(value)==expected

def test_sql_normalization_preserves_literal_semantics():
    assert normalized_sql("CREATE TABLE t( a TEXT -- field\n, b INTEGER)")==normalized_sql("create table t(a text,b integer)")
    assert normalized_sql("CHECK(a='ACTIVE')")!=normalized_sql("CHECK(a='active')")
    assert normalized_sql("CHECK(a='x -- y')")=="check(a='x -- y')"
