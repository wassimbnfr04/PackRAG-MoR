"""Verified immutable pack snapshots for the first integrated desktop slice.

Session activation is intentionally small; durable atomic install/update is M3.
Only the audited data-format library is shared with the legacy implementation.
"""
from __future__ import annotations

import sqlite3
import tempfile
import zipfile
from pathlib import Path

import numpy as np

from kpack_builder.core import PackError, canonical, sha

from .config import embedding_profile
from .validation import validate_product
from .evidence import own


class VerifiedPack:
    def __init__(self, path: Path, pinned: list[bytes], *, developer_mode: bool = False):
        self._directory = tempfile.TemporaryDirectory(prefix="packrag-verified-")
        self.root = Path(self._directory.name)
        try:
            # Validate and extract the same private snapshot, preventing path replacement races.
            snapshot = self.root / "transport.kpack"
            with path.open("rb") as source, snapshot.open("xb") as target:
                copied = 0
                while data := source.read(1024 * 1024):
                    copied += len(data)
                    if copied > 513 * 1024 * 1024:
                        raise PackError("Transport exceeds bounded import size")
                    target.write(data)
            self.audit = validate_product(snapshot, pinned, developer_mode=developer_mode)
            self.manifest = self.audit["manifest"]
            if canonical(self.manifest["embedding_profile"]) != canonical(embedding_profile()):
                raise PackError("Pack is incompatible with pinned v1.3 embedding profile")
            with zipfile.ZipFile(snapshot) as archive:
                for item in self.manifest["files"]:
                    destination = self.root / item["path"]
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    payload = archive.read(item["path"])
                    if len(payload) != item["bytes"] or sha(payload) != item["sha256"]:
                        raise PackError("Snapshot changed after validation")
                    destination.write_bytes(payload)
            self.db = sqlite3.connect(
                (self.root / "knowledge.sqlite").as_uri() + "?mode=ro&immutable=1", uri=True
            )
            self.db.row_factory = sqlite3.Row
            self.db.execute("PRAGMA trusted_schema=OFF")
            self.db.execute("PRAGMA query_only=ON")
            self.source_records=tuple(own(dict(row)) for row in self.db.execute("SELECT * FROM sources ORDER BY source_id"))
            rows = self.db.execute(
                "SELECT c.*,s.title AS source_title,s.publisher,s.sha256_original,"
                "s.jurisdiction,s.language,s.legal_status,s.effective_from AS source_from,"
                "s.effective_until_excl AS source_until,s.authority_rank,s.canonical_uri,s.document_version,s.issued_at,"
                "s.retrieved_at,s.license,s.redistribution_allowed,s.source_type,s.snapshot_path,s.notes "
                "FROM chunks c JOIN sources s USING(source_id) ORDER BY c.dense_row"
            ).fetchall()
            self.chunks = tuple(dict(row) for row in rows)
            self.by_id = {row["chunk_id"]: row for row in self.chunks}
            self.aliases = tuple(dict(row) for row in self.db.execute("SELECT * FROM aliases"))
            self.relations = tuple(dict(row) for row in self.db.execute(
                "SELECT * FROM relations ORDER BY from_chunk_id,to_chunk_id,relation_type"))
            self.derived_by_chunk = {}
            for row in self.db.execute("SELECT * FROM derived_texts ORDER BY chunk_id,purpose,language"):
                self.derived_by_chunk.setdefault(row['chunk_id'], []).append(dict(row))
            self.derived_by_chunk = {key: tuple(rows) for key, rows in self.derived_by_chunk.items()}
            self.vectors = np.empty((0,384),dtype='<f4') if not rows else np.memmap(
                self.root / "dense.kdx", mode="r", dtype="<f4", offset=84,
                shape=(len(rows), 384),
            )
        except Exception:
            self.close()
            raise

    @property
    def identity(self) -> tuple[str, str, str]:
        return (self.manifest["pack_id"], self.manifest["version"], self.audit["manifest_sha256"])

    def close(self) -> None:
        if hasattr(self, "db"):
            self.db.close()
        if isinstance(getattr(self, "vectors", None), np.memmap):
            self.vectors._mmap.close()
        self._directory.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class SessionRegistry:
    def __init__(self):
        self.active: dict[str, VerifiedPack] = {}

    def activate(self, pack: VerifiedPack) -> None:
        identity = pack.manifest["pack_id"]
        if identity in self.active:
            raise PackError("Session activation cannot replace a version; use lifecycle API")
        self.active[identity] = pack

    def snapshot(self) -> tuple[VerifiedPack, ...]:
        return tuple(self.active[key] for key in sorted(self.active))
