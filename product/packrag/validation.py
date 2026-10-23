"""Product authentication/schema ordering and staged data-format verification."""
import json
import sqlite3
import struct
import tempfile
import zipfile
from pathlib import Path

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from kpack_builder.core import (CONTROL, MAX_MANIFEST, PackError,
    bounded_read, canonical, key_id, sha)
from .database import validate_database
from .archive import audit_archive
from .config import embedding_profile, file_sha
from .manifest import require, validate_manifest
from .json_bounds import bounded_structure
from .kdx import inspect_kdx, verify_mapping


def verify_raw_manifest(raw, signature, pinned):
    require(1 <= len(pinned) <= 8 and all(type(p) is bytes and len(p) == 32 for p in pinned))
    require(len(set(pinned)) == len(pinned) and len(signature) == 64 and 0 < len(raw) <= MAX_MANIFEST)
    matches = []
    for key in pinned:
        try: VerifyKey(key).verify(raw, signature); matches.append(key)
        except BadSignatureError: pass
    require(len(matches) == 1, "Unknown signer or invalid signature")
    # Only after exact raw-byte authentication may any JSON field be interpreted.
    try:
        bounded_structure(raw)
        manifest = json.loads(raw.decode("utf-8", errors="strict"))
        require(canonical(manifest) == raw, "Noncanonical signed manifest")
        require(manifest["publisher"]["key_id"] == key_id(matches[0]), "Signer/key_id mismatch")
        return manifest
    except (ValueError, TypeError, KeyError, UnicodeError) as error:
        if isinstance(error, PackError): raise
        raise PackError("Invalid authenticated manifest: " + str(error)) from error


def authenticate_manifest(raw, signature, pinned, developer_mode):
    manifest = verify_raw_manifest(raw, signature, pinned)
    validate_manifest(manifest, embedding_profile(), developer_mode)
    return manifest


def validate_product(path: Path, pinned: list[bytes], *, developer_mode=False):
    try:
        records = audit_archive(path)
        with zipfile.ZipFile(path) as archive:
            require([(i.filename, i.CRC, i.compress_size, i.file_size, i.header_offset) for i in archive.infolist()] == [(r['name'], r['crc'], r['compressed'], r['size'], r['local']) for r in records], "ZIP library interpretation mismatch")
            raw = bounded_read(archive, "manifest.json", MAX_MANIFEST)
            manifest = authenticate_manifest(raw, bounded_read(archive, "manifest.sig", 64), pinned, developer_mode)
            require({i.filename for i in archive.infolist()} == CONTROL | {f["path"] for f in manifest["files"]}, "Undeclared/missing payload")
            with tempfile.TemporaryDirectory(prefix="packrag-validation-") as temporary:
                stage = Path(temporary)
                for file in manifest["files"]:
                    entry = archive.getinfo(file["path"])
                    require(entry.file_size == file["bytes"], "Payload declared length mismatch")
                    data = bounded_read(archive, file["path"], file["bytes"])
                    require(len(data) == file["bytes"] and sha(data) == file["sha256"], "Payload hash/length mismatch: " + file["path"])
                    target = stage / file["path"]; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
                mapping_hash=inspect_kdx(stage/'dense.kdx',manifest['embedding_profile'],manifest['counts']['chunks'])
                ids = validate_database(stage / "knowledge.sqlite", manifest, developer_mode=developer_mode)
                verify_mapping(mapping_hash,ids)
            return dict(status="PASS", manifest=manifest, manifest_sha256=sha(raw), archive_transport_sha256=file_sha(path))
    except (sqlite3.DatabaseError, zipfile.BadZipFile, KeyError, OSError, struct.error) as error:
        raise PackError(str(error)) from error
