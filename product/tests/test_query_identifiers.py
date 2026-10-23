"""Signed adjacent retrieval contracts; actual normalized Granite references.

Stored vectors test orchestration, not a rerun of encoder inference. New phone
parity and real generation gates are separately required.
"""
import json
import unicodedata
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from product.packrag.config import RuntimeContractError, file_sha
from product.packrag.packs import VerifiedPack, SessionRegistry
from product.packrag.query_unicode import contains_alias, is_word, word_terms
from product.packrag.retrieval import Query, normalize, retrieve
from product.packrag.runtime import PackRAG

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = json.loads((ROOT / "product/tests/query-contract-cases.json").read_text())
CORPUS = ROOT / "artifacts/v1.3/m4/query-identifier-fixtures-0001"
REFERENCE = json.loads((ROOT / "artifacts/v1.3/m4/relevance-references-0003/query-reference.json").read_text())


@pytest.mark.parametrize("case", CONTRACT["query_cases"], ids=lambda c: c["id"])
def test_shared_query_validation(case):
    values = [case[k] for k in ("raw", "as_of", "jurisdiction", "current_law")]
    if case["accept"]:
        query = Query(*values)
        assert query.raw == case["raw"] and query.normalized == normalize(case["raw"])
    else:
        with pytest.raises(RuntimeContractError, match=case["error"]): Query(*values)


@pytest.mark.parametrize("field,value,error", [("raw", None, "TEXT"), ("raw", 1, "TEXT"),
    ("as_of", 20261006, "DATE"), ("jurisdiction", 1, "JURISDICTION"),
    ("current_law", 1, "CURRENT_LAW"), ("current_law", "false", "CURRENT_LAW"),
    ("current_law", None, "CURRENT_LAW")])
def test_python_dynamic_types_do_not_coerce(field, value, error):
    args = dict(raw="question", as_of="2026-10-06"); args[field] = value
    with pytest.raises(RuntimeContractError, match="INVALID_QUERY_" + error): Query(**args)


def test_frozen_word_properties_and_shared_boundaries():
    assert unicodedata.unidata_version == "15.0.0"
    for point in range(0x110000):
        assert is_word(point) == (unicodedata.category(chr(point))[0] in "LN" or point == 95), hex(point)
    for case in CONTRACT["word_cases"]: assert word_terms(normalize(case["raw"])) == case["terms"]
    for case in CONTRACT["alias_cases"]: assert contains_alias(normalize(case["text"]), normalize(case["alias"])) == case["matched"]


@pytest.fixture(scope="module")
def signed_packs():
    with ExitStack() as stack:
        public = (CORPUS / "public-key.raw").read_bytes()
        packs = {}
        for record in REFERENCE["packs"]:
            path = CORPUS / record["filename"]; assert file_sha(path) == record["sha256"]
            packs[record["id"]] = stack.enter_context(VerifiedPack(path, [public], developer_mode=True))
        yield packs


@pytest.mark.parametrize("case", REFERENCE["cases"], ids=lambda c: c["id"])
def test_signed_multi_pack_orders_scores_caps_origins(case, signed_packs):
    query = Query(case["raw"], case["as_of"])
    candidates, ambiguous = retrieve(tuple(signed_packs[name] for name in case["packs"]), query, np.asarray(case["query_vector"], dtype=np.float32))
    assert ambiguous == case["expected_ambiguous"]
    assert len(candidates) == len(case["candidates"])
    for actual, expected in zip(candidates, case["candidates"], strict=True):
        assert (actual.pack.identity[0], actual.chunk["chunk_id"]) == (expected["pack_id"], expected["chunk_id"])
        assert actual.exact == expected["exact"] and actual.relevant == expected["relevant"]
        assert (actual.sparse_rank, actual.dense_rank) == (expected["sparse_rank"], expected["dense_rank"])
        assert actual.rrf == expected["rrf"]
        assert actual.dense_cosine == pytest.approx(expected["dense_cosine"], abs=1e-7)
        assert [list(o) for o in actual.origins] == expected["origins"]
        assert len(actual.origins) == len(set(actual.origins))
    # Reverse caller order cannot change representative/provenance ranking.
    reversed_candidates, reversed_ambiguous = retrieve(tuple(signed_packs[name] for name in reversed(case["packs"])), query, np.asarray(case["query_vector"], dtype=np.float32))
    assert reversed_ambiguous == ambiguous
    assert [(c.pack.identity, c.chunk["chunk_id"], c.origins) for c in reversed_candidates] == [(c.pack.identity, c.chunk["chunk_id"], c.origins) for c in candidates]


def test_runtime_normalized_embedding_and_ambiguity_prevents_generation(signed_packs):
    case = next(c for c in REFERENCE["cases"] if c["id"] == "CROSS_SOURCE_AMBIGUITY")
    seen = []
    class Encoder:
        def encode(self, text):
            seen.append(text)
            return np.asarray(case["query_vector"], dtype=np.float32)
    registry = SessionRegistry()
    for name in case["packs"]: registry.activate(signed_packs[name])
    runtime = PackRAG(registry, Encoder(), SimpleNamespace(metadata={}, generate=lambda *_: pytest.fail("Ambiguity must not generate")))
    raw = " Ａｓｔｅｒ－９ operating temperature "
    result = runtime.answer(Query(raw, "2026-10-06"))
    assert result["state"] == "IDENTIFIER_AMBIGUOUS" and seen == [normalize(raw)]
    assert result["query"]["raw"] == raw and result["query"]["normalized"] == normalize(raw)
    assert not result["selected"] and not result["citations"]
