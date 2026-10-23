"""Build a fresh synthetic development pack; never a calibrated release pack."""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import numpy as np
from nacl.signing import SigningKey

from kpack_builder.core import canonical, key_id, make_kdx, sha, validate, write_archive

from .config import embedding_profile
from .embedding import document_input


def build(destination: Path, cases: list[dict], encoder, tokenizer=None) -> dict:
    destination.mkdir(parents=True, exist_ok=False)
    db_path = destination / "knowledge.sqlite"
    schema = Path(__file__).resolve().parents[2] / "kpack_builder/schema.sql"
    ids, inputs = [], []
    with closing(sqlite3.connect(db_path)) as db, db:
        db.executescript(schema.read_text(encoding="utf-8"))
        for index, case in enumerate(cases):
            text, title, locator = case["text"], case["title"], case["locator"]
            if tokenizer is not None and len(tokenizer.tokenize(text, add_special=False)) > 500:
                raise ValueError("Development chunk exceeds actual LFM tokenizer hard cap")
            text_hash = sha(text.encode("utf-8"))
            source = "dev-" + case["id"]
            identifier = sha((source + locator + text_hash).encode("utf-8"))[:24]
            if identifier in ids:
                raise ValueError("Chunk identifier collision")
            ids.append(identifier)
            db.execute(
                "INSERT INTO sources(source_id,title,publisher,retrieved_at,language,sha256_original,"
                "license,redistribution_allowed,source_type,legal_status) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (source, title, "PackRAG synthetic development fixture", "2026-10-05", "en",
                 text_hash, "CC0-1.0", 1, "synthetic", "n/a"),
            )
            db.execute(
                "INSERT INTO chunks(chunk_id,source_id,title,section,locator,canonical_text,search_text,"
                "text_sha256,dense_row) VALUES(?,?,?,?,?,?,?,?,?)",
                (identifier, source, title, locator, locator, text, text, text_hash, index),
            )
            for alias in case["aliases"]:
                from .retrieval import normalize
                db.execute("INSERT INTO aliases VALUES(?,?,?,?,?)",
                           (alias, normalize(alias), "chunk", identifier, "equipment-model"))
            inputs.append(document_input(title, locator, "", text))
        db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
    vectors = np.asarray([encoder.encode(text) for text in inputs], dtype=np.float32)
    profile = embedding_profile()
    signer = SigningKey.generate()  # Fresh, ephemeral development signer; no private seed persisted.
    public = bytes(signer.verify_key)
    (destination / "developer-public-key.raw").write_bytes(public)
    manifest = dict(
        schema_version="1.0", pack_id="org.packrag.development.walking-skeleton", name="Synthetic v1.3 development pack",
        version="0.1.0", release_timestamp="2026-10-05T00:00:00Z",
        publisher=dict(name="PackRAG DEVELOPMENT ONLY", key_id=key_id(public)), languages=["en"],
        jurisdictions=[], domain="repair", freshness=dict(update_check_after="2027-01-01", stale_behavior="warn-and-continue"),
        embedding_profile=profile, compatible_retrieval_profile="mobile-v1",
        generator_compatibility=dict(core_api="1.x", preferred_generator_language="en", neural_cache_required=False),
        counts=dict(sources=len(cases), chunks=len(cases), relations=0),
        calibration=dict(status="UNCALIBRATED", dataset_sha256=None, method="candidate-relevance-v1.3",
                         min_agreed_dense_cosine=None, min_dense_only_cosine=None, precision=None, recall=None),
        build=dict(builder_version="1.3.0-dev", normalizer_version="1.0.0", chunker_version="development-frozen-facts-1",
                   source_manifest_sha256=sha(canonical(cases)), build_input_sha256=sha(canonical(inputs))), files=[],
    )
    path = destination / "walking-skeleton.kpack"
    write_archive(path, manifest, {"knowledge.sqlite": db_path.read_bytes(), "dense.kdx": make_kdx(vectors, profile, ids)}, signer)
    result = validate(path, [public], developer_mode=True)
    provenance = dict(purpose="SYNTHETIC_DEVELOPMENT_NOT_RELEASE_CALIBRATION", cases=cases,
                      input_recipe=profile["input_construction"], embedding_inputs=inputs, profile=profile,
                      source_identities=dict(original_texts_sha256=sha(canonical(cases))),
                      signer_private_seed="EPHEMERAL_NOT_SAVED", **{key: value for key, value in result.items() if key != "manifest"})
    (destination / "build-provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"path": path, "public_key": public, "audit": result}
