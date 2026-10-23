import json
import zipfile
from pathlib import Path
import pytest
from kpack_builder.core import PackError,sha
from product.packrag.config import file_sha
from product.packrag.json_bounds import bounded_structure
from product.packrag.packs import VerifiedPack
from product.packrag import validation

FOLDER = Path(__file__).resolve().parents[2]/"artifacts/v1.3/m3/security-fixtures-0001"
CORPUS = json.loads((FOLDER/"cases.json").read_text(encoding="utf-8"))
VECTORS = json.loads((FOLDER/"raw-vectors.json").read_text(encoding="utf-8"))
BOUNDS = json.loads((FOLDER/"bounds-cases.json").read_text(encoding="utf-8"))

@pytest.mark.parametrize("case",CORPUS["cases"],ids=lambda c:c["id"])
def test_signed_residual_security_corpus_actual_import(case,monkeypatch):
    path=FOLDER/case["filename"]; key=(FOLDER/"public-key.raw").read_bytes()
    assert file_sha(path)==case["sha256"]
    def forbidden(*args,**kwargs): raise AssertionError("Rejected input reached a later interpretation stage")
    if case["group"]=="AUTH_RAW": monkeypatch.setattr(validation,"bounded_structure",forbidden)
    if case["group"] in ("AUTH_RAW","HASH_TAMPER","JSON_BOUND","IDENTITY_BOUND") and not case["accept"]:
        monkeypatch.setattr(validation,"validate_database",forbidden)
    if case["group"]=="JSON_BOUND": monkeypatch.setattr(validation.json,"loads",forbidden)
    if case['group']=='KDX_STRUCTURAL' and not case['accept'] and case['id']!='kdx-mapping-hash':
        monkeypatch.setattr(validation,'validate_database',forbidden)
    if case["accept"]:
        with VerifiedPack(path,[key],developer_mode=True) as pack:
            assert len(pack.chunks)==10 and pack.vectors.shape==(10,384)
    else:
        with pytest.raises(PackError,match=case.get("error_contains")):
            VerifiedPack(path,[key],developer_mode=True)
    assert file_sha(path)==case["sha256"]

def test_db_kdx_one_byte_tamper_has_correct_crc_unchanged_signed_manifest():
    with zipfile.ZipFile(FOLDER/"valid.kpack") as baseline:
        for name in ("knowledge.sqlite","dense.kdx"):
            path=FOLDER/("one-byte-"+name.replace(".","-")+".kpack")
            with zipfile.ZipFile(path) as changed:
                assert changed.testzip() is None
                assert changed.read("manifest.json")==baseline.read("manifest.json")
                assert changed.read("manifest.sig")==baseline.read("manifest.sig")
                a,b=baseline.read(name),changed.read(name)
                assert len(a)==len(b) and sum(x!=y for x,y in zip(a,b,strict=True))==1
                assert sha(a)!=sha(b)

@pytest.mark.parametrize("case",VECTORS["cases"],ids=lambda c:c["id"])
def test_raw_signature_bounded_json_contract(case,monkeypatch):
    raw=bytes.fromhex(case["raw_hex"]); sig=bytes.fromhex(case["signature_hex"]); key=bytes.fromhex(VECTORS["public_key_hex"])
    if case["id"]=="unknown-before-depth":
        def forbidden(*args): raise AssertionError("Unauthenticated input reached structural scanner")
        monkeypatch.setattr(validation,"bounded_structure",forbidden)
    if case["accept"]: assert validation.verify_raw_manifest(raw,sig,[key])["publisher"]["key_id"]=="ed25519:"+sha(key)
    else:
        with pytest.raises(PackError,match=case.get("error_contains")): validation.verify_raw_manifest(raw,sig,[key])

@pytest.mark.parametrize("case",BOUNDS,ids=lambda c:c["id"])
def test_shared_json_lexical_bound_cases(case):
    if case["accept"]: bounded_structure(case["raw"].encode())
    else:
        with pytest.raises(PackError): bounded_structure(case["raw"].encode())

def test_eight_distinct_pinned_keys_match_exactly_one_and_key_sets_fail_closed():
    fleet=[bytes.fromhex(x) for x in VECTORS["eight_distinct_public_keys_hex"]]; assert len(fleet)==len(set(fleet))==8
    case=VECTORS["cases"][0]; raw=bytes.fromhex(case["raw_hex"]); sig=bytes.fromhex(case["signature_hex"])
    assert validation.verify_raw_manifest(raw,sig,fleet)["version"]=="1.1.0"
    for keys in (fleet[:-1],fleet+[fleet[0]],fleet[:-1]+[fleet[0]],[fleet[-1][:-1]],[]):
        with pytest.raises(PackError): validation.verify_raw_manifest(raw,sig,keys)
