"""Frozen product identities and configuration, verified before runtime activation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "config/toolchain.lock.json").read_text(encoding="utf-8"))
PROFILE = json.loads((ROOT / "config/runtime-profile.json").read_text(encoding="utf-8"))


class RuntimeContractError(ValueError):
    pass


def file_sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_file(path: Path, expected: str) -> None:
    if file_sha(path) != expected:
        raise RuntimeContractError(f"Asset hash mismatch: {path.name}")


def embedding_profile() -> dict:
    embedder = LOCK["embedder"]
    if embedder.get("asset_hash_status") != "VERIFIED":
        raise RuntimeContractError("Pinned embedding assets not verified")
    return embedder["pack_profile"]
