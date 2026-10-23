"""Fixed-schema disposable SQLite validation; never mutates the signed original."""
import math
import re
import shutil
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from kpack_builder.core import PackError, sha
from .archive import safe_path
from .config import file_sha
from .languages import valid_tag
from .manifest import require
from .normalization import normalize
from .temporal import iso_date, date_or_timestamp

TABLES = ("sources", "chunks", "relations", "aliases", "derived_texts")
RELATIONS = set("parent child cites see_also amends supersedes exception_to requires procedure_next procedure_previous".split())


def normalized_sql(sql):
    tokens = re.findall(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|--[^\n]*|/\*.*?\*/|[^\s]", sql, re.S)
    return "".join(t if t.startswith(("'",'"')) else t.lower() for t in tokens if not t.startswith(("--","/*")))


def validate_metadata(db, manifest, payload_root, developer_mode):
    data = {t: [dict(row) for row in db.execute("SELECT * FROM "+t)] for t in TABLES}
    languages = {i.lower() for i in manifest["languages"]}
    jurisdictions = set(manifest["jurisdictions"])
    declared = {i["path"]: i for i in manifest["files"]}
    def text(v): require(type(v) is str and bool(v.strip()), "Empty required DB text")
    def hash_(v): require(type(v) is str and re.fullmatch(r"[0-9a-f]{64}",v), "Invalid DB hash")
    def interval(row):
        a, b = row["effective_from"],row["effective_until_excl"]
        for v in (a,b):
            if v is not None: iso_date(v)
        require(a is None or b is None or a < b, "Invalid DB validity interval")
    source_ids = set(); chunk_ids = set()
    for row in data["sources"]:
        for key in ("source_id","title","publisher","retrieved_at","language","license","source_type"): text(row[key])
        require(row["source_id"] not in source_ids); source_ids.add(row["source_id"])
        date_or_timestamp(row["retrieved_at"])
        if row["issued_at"] is not None: date_or_timestamp(row["issued_at"])
        interval(row); hash_(row["sha256_original"])
        require(valid_tag(row["language"]) and row["language"].lower() in languages, "Undeclared source language")
        require(row["jurisdiction"] is None or row["jurisdiction"] in jurisdictions, "Undeclared source jurisdiction")
        require(row["redistribution_allowed"] in (0,1))
        require(row["authority_rank"] is None or 0 <= row["authority_rank"] <= 2147483647)
        require(row["legal_status"] is None or row["legal_status"] in ("active","superseded","repealed","historical","n/a"))
        snapshot = row["snapshot_path"]
        if snapshot is not None:
            safe_path(snapshot); require(snapshot.startswith("sources/") and snapshot in declared, "Invalid snapshot provenance path")
            require(file_sha(payload_root/snapshot) == row["sha256_original"], "Snapshot/original source hash mismatch")
    for row in data["chunks"]:
        for key in ("chunk_id","source_id","locator","canonical_text","search_text"): text(row[key])
        require(row["chunk_id"] not in chunk_ids); chunk_ids.add(row["chunk_id"])
        require(row["source_id"] in source_ids); interval(row); hash_(row["text_sha256"])
        require(sha(row["canonical_text"].encode("utf-8")) == row["text_sha256"])
        for start,end,minimum in (("page_start","page_end",1),("character_start","character_end",0)):
            for key in (start,end):
                if row[key] is not None: require(minimum <= row[key] <= 2147483647)
            require(row[start] is None or row[end] is None or row[start] <= row[end], "Reversed DB location bounds")
    for row in data["relations"]:
        require(row["from_chunk_id"] in chunk_ids and row["to_chunk_id"] in chunk_ids, "Dangling relation target")
        require(row["relation_type"] in RELATIONS and row["provenance"] in ("explicit-reference","structure","curated"))
        require(type(row["confidence"]) in (int,float) and math.isfinite(row["confidence"]) and 0 <= row["confidence"] <= 1)
    for row in data["aliases"]:
        for key in ("alias","normalized_alias","target_type","target_id","alias_type"): text(row[key])
        require(row["normalized_alias"] == normalize(row["alias"]), "Noncanonical alias normalization")
        require(row["target_type"] in ("source","chunk"))
        require(row["target_id"] in (source_ids if row["target_type"] == "source" else chunk_ids), "Dangling alias target")
    for row in data["derived_texts"]:
        for key in ("chunk_id","purpose","language","text","text_sha256","derivation_method"): text(row[key])
        require(row["chunk_id"] in chunk_ids and row["purpose"] == "generator")
        require(valid_tag(row["language"]) and row["language"].lower() in languages)
        hash_(row["text_sha256"]); require(sha(row["text"].encode("utf-8")) == row["text_sha256"])
        method = row["derivation_method"]
        require(method in ("official_translation","human_reviewed_translation","machine_draft"))
        require(developer_mode or method != "machine_draft", "Machine draft cannot ship as release evidence")
        if method != "machine_draft": text(row["derivation_source"])
        if method == "human_reviewed_translation": text(row["reviewer_id"]); text(row["reviewed_at"]); date_or_timestamp(row["reviewed_at"])


def validate_database(original, manifest, *, developer_mode=False):
    before = file_sha(original)
    schema = Path(__file__).resolve().parents[2]/"kpack_builder/schema.sql"
    try:
        with tempfile.TemporaryDirectory(prefix="packrag-db-") as temporary:
            copy = Path(temporary)/"validation.sqlite"; shutil.copyfile(original,copy)
            with closing(sqlite3.connect(copy)) as db, closing(sqlite3.connect(":memory:")) as expected:
                db.execute("PRAGMA trusted_schema=OFF")
                require(db.execute("PRAGMA integrity_check").fetchall() == [("ok",)], "SQLite integrity failure")
                require(not db.execute("PRAGMA foreign_key_check").fetchall(), "SQLite foreign-key failure")
                expected.executescript(schema.read_text(encoding="utf-8"))
                actual_objects = db.execute("SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
                expected_objects = expected.execute("SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
                require({(t,n) for t,n,_ in actual_objects} == {(t,n) for t,n,_ in expected_objects}, "Unexpected/missing DB object")
                actual_sql = {n:s for _,n,s in actual_objects}; expected_sql = {n:s for _,n,s in expected_objects}
                for name in (*TABLES,"chunks_fts","aliases_norm_idx"):
                    require(normalized_sql(actual_sql[name]) == normalized_sql(expected_sql[name]), "Full DB schema mismatch: "+name)
                for table in TABLES:
                    columns = expected.execute("PRAGMA table_info("+table+")").fetchall()
                    require(db.execute("PRAGMA table_info("+table+")").fetchall()==columns)
                    require(db.execute("PRAGMA foreign_key_list("+table+")").fetchall()==expected.execute("PRAGMA foreign_key_list("+table+")").fetchall())
                    types = db.execute("SELECT "+",".join("typeof("+c[1]+")" for c in columns)+" FROM "+table).fetchall()
                    for values in types:
                        for c,kind in zip(columns,values):
                            require(kind == "null" or kind in {"TEXT":("text",),"INTEGER":("integer",),"REAL":("real","integer")}[c[2]], "DB storage type mismatch")
                db.execute("INSERT INTO chunks_fts(chunks_fts,rank) VALUES('integrity-check',1)")
                for table in ("sources","chunks","relations"):
                    require(db.execute("SELECT count(*) FROM "+table).fetchone()[0] == manifest["counts"][table], "DB count mismatch")
                require(db.execute("SELECT count(*) FROM chunks_fts").fetchone()[0] == manifest["counts"]["chunks"])
                mapping = db.execute("SELECT chunk_id,dense_row FROM chunks ORDER BY dense_row").fetchall()
                require([r[1] for r in mapping] == list(range(len(mapping))), "Invalid dense mapping")
                db.row_factory = sqlite3.Row
                validate_metadata(db,manifest,original.parent,developer_mode)
                ids = [r[0] for r in mapping]
        require(file_sha(original) == before, "Original DB changed")
        return ids
    except (sqlite3.DatabaseError, UnicodeError, ValueError, TypeError, KeyError) as error:
        if isinstance(error,PackError): raise
        raise PackError("Invalid DB: "+str(error)) from error
