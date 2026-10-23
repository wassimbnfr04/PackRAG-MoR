"""New signed synthetic packs and actual normalized-Granite retrieval references.

No release calibration, human source review or PackBench/gold labels. Fixture
signer is ephemeral; originals are explicitly synthetic byte identities.
"""
import argparse
import hashlib
import json
import shutil
import sqlite3
from contextlib import ExitStack, closing
from pathlib import Path

import numpy as np
from nacl.signing import SigningKey
from kpack_builder.core import canonical, key_id, make_kdx, sha, write_archive
from product.packrag.config import embedding_profile, file_sha
from product.packrag.embedding import GraniteEncoder, document_input
from product.packrag.normalization import normalize
from product.packrag.packs import VerifiedPack
from product.packrag.retrieval import Query, retrieve, retrieve_pack

ROOT = Path(__file__).resolve().parents[1]


def make_pack(run, name, chunks, encoder, signer):
    directory = run / name
    directory.mkdir()
    db_path = directory / "knowledge.sqlite"
    vectors, ids, sources = [], [], {}
    with closing(sqlite3.connect(db_path)) as db, db:
        db.executescript((ROOT / "kpack_builder/schema.sql").read_text())
        for index, row in enumerate(chunks):
            source = row.get("source", f"{name}-{row['id']}")
            original = row.get("original", row["text"])
            if source not in sources:
                sources[source] = sha(original.encode())
                db.execute("INSERT INTO sources(source_id,title,publisher,retrieved_at,language,sha256_original,license,redistribution_allowed,source_type,legal_status,effective_until_excl) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (source, row["title"], "SYNTHETIC PackRAG contract fixture", "2026-10-06", "en", sources[source], "CC0-1.0", 1, "synthetic", "n/a", row.get("until")))
            text_hash = sha(row["text"].encode())
            locator = row.get("locator", row["id"])
            identifier = sha((source + locator + text_hash).encode())[:24]
            assert identifier not in ids
            ids.append(identifier)
            db.execute("INSERT INTO chunks(chunk_id,source_id,title,section,locator,canonical_text,search_text,text_sha256,dense_row) VALUES(?,?,?,?,?,?,?,?,?)",
                (identifier, source, row["title"], locator, locator, row["text"], row["text"], text_hash, index))
            for alias in row.get("aliases", []):
                db.execute("INSERT OR IGNORE INTO aliases VALUES(?,?,?,?,?)", (alias, normalize(alias), row.get("target_type", "chunk"), source if row.get("target_type") == "source" else identifier, "synthetic-identifier"))
            vectors.append(encoder.encode(document_input(row["title"], locator, "", row["text"])))
        db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
    profile = embedding_profile()
    manifest = dict(schema_version="1.0", pack_id="org.packrag.contract." + name, name="SYNTHETIC " + name,
        version="1.0.0", release_timestamp="2026-10-06T00:00:00Z",
        publisher=dict(name="EPHEMERAL TEST ONLY", key_id=key_id(bytes(signer.verify_key))), languages=["en"], jurisdictions=[], domain="repair",
        freshness=dict(update_check_after="2027-01-01", stale_behavior="warn-and-continue"), embedding_profile=profile,
        compatible_retrieval_profile="mobile-v1", generator_compatibility=dict(core_api="1.x", preferred_generator_language="en", neural_cache_required=False),
        counts=dict(sources=len(sources), chunks=len(chunks), relations=0),
        calibration=dict(status="UNCALIBRATED", dataset_sha256=None, method="candidate-relevance-v1.3", min_agreed_dense_cosine=None, min_dense_only_cosine=None, precision=None, recall=None),
        build=dict(builder_version="1.3.0-contract", normalizer_version="1.0.0", chunker_version="synthetic-contract-1", source_manifest_sha256=sha(canonical(chunks))), files=[])
    path = run / (name + ".kpack")
    write_archive(path, manifest, {"knowledge.sqlite": db_path.read_bytes(), "dense.kdx": make_kdx(np.asarray(vectors, dtype=np.float32), profile, ids)}, signer)
    return path, ids


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(); run = args.run.resolve()
    assert run.is_relative_to(ROOT); run.mkdir(parents=True, exist_ok=False)
    asset = ROOT / "product/android/app/src/androidTest/assets/query-identifier-corpus"
    assert not asset.exists()
    encoder = GraniteEncoder(ROOT / "models/v1.3/granite")
    signer = SigningKey.generate(); public = bytes(signer.verify_key)
    (run / "public-key.raw").write_bytes(public)
    thermal = dict(id="thermal", title="Aster-9", text="The Aster-9 thermal controller has a maximum continuous operating temperature of 74 °C.", aliases=["Aster-9"])
    primary = [thermal] + [dict(id=f"unit{i:02}", title=f"Unit-{i:02}", text=f"Unit-{i:02} equipment has an inspection interval of {i+10} hours.", aliases=[f"Unit-{i:02}"]) for i in range(42)]
    primary.append(dict(id="lost", title="Garden", text="Garden flowers grow beside an ornamental pond.", aliases=["LOST"]))
    twin = [{**row, "source": "different-local-" + row["id"]} for row in primary]
    distinct = [dict(id=f"other{i:02}", title=f"Control-{i:02}", text=f"Control-{i:02} equipment has a maintenance interval of {i+50} hours.", aliases=[f"Control-{i:02}"]) for i in range(42)]
    shared_original = "Synthetic manual: thermal limits are 74 °C. Inspect the cable before use."
    shared = [{**thermal, "source": "shared-manual", "original": shared_original, "target_type": "source"},
              dict(id="cable", title="Aster-9", text="Inspect the cable before using the Aster-9.", aliases=["Aster-9"], source="shared-manual", original=shared_original, target_type="source")]
    within = [{**thermal, "source": "same-manual", "locator": "first"}, {**thermal, "id": "second", "source": "same-manual", "locator": "second"}]
    collision = [{**thermal, "text": "The different Aster-9 instrument operates up to 37 °C."}]
    lost = [dict(id="lost-other", title="Other garden", text="The LOST identifier names a different synthetic source.", aliases=["LOST"])]
    specifications = {"primary": primary, "twin": twin, "distinct": distinct, "source-alias": shared,
        "within-duplicate": within, "collision": collision, "expired": [{**collision[0], "until": "2026-01-01"}], "lost-collision": lost}
    paths, chunk_ids, records = {}, {}, []
    for name, chunks in specifications.items():
        paths[name], chunk_ids[name] = make_pack(run, name, chunks, encoder, signer)
        records.append(dict(id=name, filename=paths[name].name, sha256=file_sha(paths[name]), chunks=len(chunks)))
    multi_query = " ".join(f"Unit-{i:02}" for i in range(42)) + " LOST"
    scenarios = [
        ("NORMALIZED_FULLWIDTH", ["primary"], "Ｗｈａｔ is the Ａｓｔｅｒ－９ operating temperature?", False),
        ("CROSS_SOURCE_AMBIGUITY", ["primary", "collision"], "Aster-9 operating temperature", True),
        ("DUPLICATE_ORIGINAL_DIFFERENT_LOCAL_IDS", ["primary", "twin"], "Aster-9 operating temperature", False),
        ("SOURCE_ALIAS_MULTIPLE_SECTIONS", ["source-alias"], "Aster-9 operating temperature", False),
        ("WITHIN_PACK_DEDUP_ORIGIN_UNIQUE", ["within-duplicate"], "Aster-9 operating temperature", False),
        ("INELIGIBLE_COLLISION_IGNORED", ["primary", "expired"], "Aster-9 operating temperature", False),
        ("CROSS_POOL_32_CAP", ["primary", "distinct"], "equipment inspection maintenance interval", False),
        ("AMBIGUITY_BEFORE_LOCAL_CAP", ["primary", "lost-collision"], multi_query, True),
        ("DIFFERENT_ALIASES_NOT_AMBIGUOUS", ["primary", "distinct"], "Aster-9 and Control-00", False),
        ("ALIAS_NOT_SUBSTRING", ["primary"], "Aster-90", False),
    ]
    references = []
    with ExitStack() as stack:
        packs = {name: stack.enter_context(VerifiedPack(path, [public], developer_mode=True)) for name, path in paths.items()}
        for identity, selected, raw, expected in scenarios:
            query = Query(raw, "2026-10-06"); vector = encoder.encode(query.normalized)
            active = tuple(packs[name] for name in selected)
            candidates, ambiguous = retrieve(active, query, vector)
            assert ambiguous == expected, identity
            if identity == "AMBIGUITY_BEFORE_LOCAL_CAP":
                local, _ = retrieve_pack(packs["primary"], query, vector)
                assert chunk_ids["primary"][-1] not in [c.chunk["chunk_id"] for c in local], "Fixture must exercise a collision discarded by local cap"
            if identity == "CROSS_POOL_32_CAP": assert len(candidates) == 32
            if identity == "WITHIN_PACK_DEDUP_ORIGIN_UNIQUE": assert len(candidates) == 1 and len(candidates[0].origins) == 1
            if identity == "ALIAS_NOT_SUBSTRING": assert not any(c.exact for c in candidates)
            rows = [dict(pack_id=c.pack.identity[0], chunk_id=c.chunk["chunk_id"], exact=c.exact,
                sparse_rank=c.sparse_rank, dense_rank=c.dense_rank, dense_cosine=c.dense_cosine, rrf=c.rrf,
                relevant=c.relevant, origins=[list(o) for o in c.origins]) for c in candidates]
            references.append(dict(id=identity, packs=selected, raw=raw, normalized=query.normalized,
                as_of=query.as_of, expected_ambiguous=expected, query_vector=vector.tolist(), candidates=rows))
    record = dict(status="REFERENCES_FROZEN_NOT_DEVICE_OR_GENERATION_ACCEPTANCE", purpose="SYNTHETIC_QUERY_ALIAS_DEDUP_CAPS_WITH_ACTUAL_GRANITE_NOT_RELEASE_CALIBRATION", private_seed="EPHEMERAL_NOT_SAVED", script_sha256=file_sha(Path(__file__)), packs=records, cases=references, unicode_table_sha256=file_sha(ROOT / "product/config/query-unicode15.json"), embedder_profile=embedding_profile(), public_key_sha256=file_sha(run / "public-key.raw"))
    (run / "cases.json").write_text(json.dumps(record, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    asset.mkdir()
    for path in [run / "cases.json", run / "public-key.raw", *paths.values()]: shutil.copyfile(path, asset / path.name)
    print("Frozen", len(records), "signed packs and", len(references), "normalized actual-Granite retrieval cases")


if __name__ == "__main__": main()
