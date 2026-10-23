import copy
import json
import zipfile
from pathlib import Path

import pytest
from kpack_builder.core import PackError
from product.packrag.config import embedding_profile
from product.packrag.manifest import compare_versions, validate_manifest, version

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads(Path(__file__).with_name("manifest-cases.json").read_text())


def mutate_manifest(base, case):
    value = copy.deepcopy(base)
    if case.get("calibrated"):
        value["calibration"] = dict(method="candidate-relevance-v1.3", dataset_sha256="a"*64,
            min_agreed_dense_cosine=0.5, min_dense_only_cosine=0.8, precision=0.9, recall=0.8)
    for path, replacement in case.get("sets", []):
        parent = value
        for key in path[:-1]: parent = parent[key]
        parent[path[-1]] = replacement
    for path in case.get("removes", []):
        parent = value
        for key in path[:-1]: parent = parent[key]
        del parent[path[-1]]
    return value


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_shared_manifest_semantic_corpus(case):
    with zipfile.ZipFile(ROOT/"artifacts/v1.3/m1/smoke-0001/developer-pack/walking-skeleton.kpack") as z:
        base = json.loads(z.read("manifest.json"))
    candidate = mutate_manifest(base, case)
    if case["accept"]:
        validate_manifest(candidate, embedding_profile(), case.get("developer_mode", True))
    else:
        with pytest.raises(PackError): validate_manifest(candidate, embedding_profile(), case.get("developer_mode", True))


def test_semver_precedence_not_lexical():
    order = ["1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta", "1.0.0-beta", "1.0.0-beta.2", "1.0.0-beta.11", "1.0.0-rc.1", "1.0.0", "1.0.2", "1.0.10", "2.0.0"]
    for a, b in zip(order, order[1:]):
        assert compare_versions(a,b) < 0 and compare_versions(b,a) > 0
    assert compare_versions("1.0.0+old", "1.0.0+new") == 0
    assert compare_versions("1.0.0-99999999999999999999999", "1.0.0-100000000000000000000000") < 0
    for invalid in ["1.0", "1.0.0-01", "1.0.0+", "1.0.0-a..b"]:
        with pytest.raises(PackError): version(invalid)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_signed_transport_corpus_and_adjacent_real_db_kdx(case, monkeypatch):
    from product.packrag import validation
    from product.packrag.packs import VerifiedPack
    corpus = ROOT/"artifacts/v1.3/m3/manifest-fixtures-0001"
    public = (corpus/"public-key.raw").read_bytes()
    path = corpus/(case["id"]+".kpack")
    # Invalid authenticated semantics must reject before any DB parser is invoked.
    if not case["accept"]:
        def forbidden_db(*args): raise AssertionError("Invalid manifest reached DB interpretation")
        monkeypatch.setattr(validation, "validate_database", forbidden_db)
        with pytest.raises(PackError): VerifiedPack(path,[public],developer_mode=case.get("developer_mode",True))
    else:
        with VerifiedPack(path,[public],developer_mode=case.get("developer_mode",True)) as pack:
            assert len(pack.chunks)==10 and pack.vectors.shape==(10,384)


def test_new_product_authentication_before_json_and_db(monkeypatch):
    from nacl.signing import SigningKey
    from product.packrag import validation
    signer = SigningKey.generate(); public = bytes(signer.verify_key)
    raw = b"not even JSON"; signature = signer.sign(raw).signature
    def forbidden_json(*args, **kwargs): raise AssertionError("Unauthenticated bytes reached JSON parser")
    with monkeypatch.context() as patch:
        patch.setattr(validation.json, "loads", forbidden_json)
        for message, sig, keys in [(raw+b"x",signature,[public]),(raw,signature,[bytes(SigningKey.generate().verify_key)]),
                                  (raw,signature[:63],[public]),(raw,signature,[public,public]),
                                  (raw,signature,[]),(raw,signature,[public]*9)]:
            with pytest.raises(PackError): validation.authenticate_manifest(message,sig,keys,True)
    # Even a valid signer cannot authorize malformed UTF-8, JSON or noncanonical bytes.
    for message in [b"\xff",b"not JSON",b'{"duplicate":1,"duplicate":2}',b'{"a": NaN}']:
        with pytest.raises(PackError): validation.authenticate_manifest(message,signer.sign(message).signature,[public],True)
