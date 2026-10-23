"""Bounded classic ZIP transport with matching local/central records.

Small forced-ZIP64 local records are supported; ZIP64 central directories are
unnecessary under the application caps and are rejected. No payload is parsed
here. Authentication and signed payload hashes remain separate mandatory gates.
"""
import re
import struct
import unicodedata
import zlib
from pathlib import Path
from .errors import require
from .portable_names import fold

MAX_ENTRY = 256 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
MAX_TRANSPORT = MAX_TOTAL + 1024 * 1024
CONTROL = {"manifest.json", "manifest.sig"}
SOURCE_TYPES = {
    "txt": "text/plain", "md": "text/markdown", "pdf": "application/pdf",
    "csv": "text/csv", "tsv": "text/tab-separated-values", "json": "application/json",
    "xml": "application/xml", "png": "image/png", "jpg": "image/jpeg",
    "jpeg": "image/jpeg", "webp": "image/webp",
}


def allowed_media_type(path, media_type):
    """Signed metadata can describe only the admitted data format or opaque data."""
    safe_path(path)
    expected = {"knowledge.sqlite": "application/vnd.sqlite3", "dense.kdx": "application/octet-stream"}.get(path)
    if path.startswith("sources/"):
        expected = SOURCE_TYPES[path.rsplit(".", 1)[-1].lower()]
    require(media_type.lower() in {expected, "application/octet-stream"}, "Payload media type not allow-listed")


def safe_path(path):
    require(type(path) is str and bool(path) and not path.startswith("/") and "\\" not in path and ":" not in path, "Unsafe ZIP path")
    require(unicodedata.normalize("NFC", path) == path and len(path.encode("utf-8")) <= 4096, "Nonportable ZIP path")
    for part in path.split("/"):
        require(part not in ("", ".", "..") and not part.endswith((".", " ")) and len(part.encode("utf-8")) <= 255, "Unsafe ZIP segment")
        require(not any(ord(c) < 32 or ord(c) == 127 or c in '<>"|?*' for c in part), "Unsafe ZIP character")
        require(not re.fullmatch(r"(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part, re.I), "Reserved ZIP name")
    require(path in CONTROL | {"knowledge.sqlite", "dense.kdx"} or path.startswith("sources/"), "Forbidden payload location")
    if path.startswith("sources/"):
        name = path.rsplit("/", 1)[-1]
        require("." in name and name.rsplit(".", 1)[-1].lower() in SOURCE_TYPES, "Source data type not allow-listed")


def _extras(data, name):
    fields = {}; offset = 0
    while offset < len(data):
        require(offset + 4 <= len(data), "Truncated ZIP extra")
        tag, size = struct.unpack_from("<HH", data, offset); offset += 4
        require(offset + size <= len(data) and tag not in fields, "Invalid/duplicate ZIP extra")
        fields[tag] = data[offset:offset + size]; offset += size
    require(not ({0x0017, 0x9901} & fields.keys()), "Encrypted ZIP extra")
    if 0x7075 in fields:
        value = fields[0x7075]
        require(len(value) >= 5 and value[0] == 1 and struct.unpack_from("<I", value, 1)[0] == zlib.crc32(name) and value[5:] == name, "Ambiguous Unicode ZIP path")
    return fields


def audit_archive(path: Path):
    with path.open("rb") as stream:
        length = path.stat().st_size
        require(22 <= length <= MAX_TRANSPORT, "Invalid ZIP transport size")
        def read(offset, count, end=length):
            require(0 <= offset <= end and 0 <= count <= end - offset, "ZIP record outside bounds")
            stream.seek(offset); result = stream.read(count)
            require(len(result) == count, "Truncated ZIP record")
            return result
        tail_offset = max(0, length - 65557); tail = read(tail_offset, length - tail_offset)
        ends = [i for i in range(len(tail) - 22, -1, -1) if tail[i:i+4] == b"PK\x05\x06" and i + 22 + struct.unpack_from("<H", tail, i+20)[0] == len(tail)]
        require(len(ends) == 1, "Missing/ambiguous ZIP end")
        end = tail_offset + ends[0]
        disk, cd_disk, disk_count, count, cd_length, cd_offset = struct.unpack_from("<HHHHII", tail, ends[0]+4)
        require(disk == cd_disk == 0 and disk_count == count and 2 <= count <= 5000 and cd_offset + cd_length == end, "Unsupported ZIP directory")
        offset = cd_offset; records = []; seen = set(); total = 0
        for _ in range(count):
            fixed = read(offset, 46, end); require(fixed[:4] == b"PK\x01\x02", "Invalid central record")
            version, flags, method = struct.unpack_from("<HHH", fixed, 6)
            crc, compressed, size = struct.unpack_from("<III", fixed, 16)
            nl, el, cl, entry_disk = struct.unpack_from("<HHHH", fixed, 28)
            attrs, local = struct.unpack_from("<II", fixed, 38)
            require(version in (10, 20, 45) and not flags & ~0x080E and method in (0, 8) and (method != 0 or not flags & 6), "Unsupported ZIP feature")
            require(entry_disk == 0 and (attrs >> 16) & 0xF000 in (0, 0x8000) and not attrs & 0x10, "Nonregular/split ZIP entry")
            require(size <= MAX_ENTRY and compressed <= MAX_TRANSPORT and (method != 0 or compressed == size), "ZIP entry size")
            total += size; require(total <= MAX_TOTAL, "ZIP total size")
            name = read(offset+46, nl, end); extra = read(offset+46+nl, el, end)
            try: decoded = name.decode("utf-8", errors="strict")
            except UnicodeError: require(False, "Invalid UTF-8 ZIP path")
            require(flags & 0x800 or all(b < 128 for b in name), "Missing UTF-8 ZIP flag")
            safe_path(decoded); require(fold(decoded) not in seen, "Duplicate ZIP name"); seen.add(fold(decoded))
            require(1 not in _extras(extra, name), "ZIP64 central directory forbidden by caps")
            records.append(dict(name=decoded, raw=name, flags=flags, method=method, crc=crc, compressed=compressed, size=size, local=local, version=version))
            offset += 46 + nl + el + cl; require(offset <= end, "Central record overflow")
        require(offset == end, "Trailing central records")
        names = {r["name"] for r in records}; require(CONTROL <= names, "Missing controls")
        require(next(r["size"] for r in records if r["name"] == "manifest.json") <= 1024*1024 and next(r["size"] for r in records if r["name"] == "manifest.sig") == 64, "Invalid control sizes")
        cursor = 0
        for r in sorted(records, key=lambda r: r["local"]):
            require(r["local"] == cursor, "Overlapping/hidden ZIP local records")
            fixed = read(cursor, 30, cd_offset); require(fixed[:4] == b"PK\x03\x04", "Invalid local record")
            version, flags, method = struct.unpack_from("<HHH", fixed, 4)
            crc, compressed, size = struct.unpack_from("<III", fixed, 14)
            nl, el = struct.unpack_from("<HH", fixed, 26)
            require((version, flags, method) == (r["version"], r["flags"], r["method"]), "Local/central feature mismatch")
            name = read(cursor+30, nl, cd_offset); require(name == r["raw"], "Local/central path mismatch")
            extra = _extras(read(cursor+30+nl, el, cd_offset), name)
            zip64 = compressed == 0xFFFFFFFF or size == 0xFFFFFFFF
            if zip64:
                require(version == 45 and 1 in extra, "Missing local ZIP64 sizes")
                values = extra[1]; position = 0
                if size == 0xFFFFFFFF:
                    require(position+8 <= len(values), "Short ZIP64 size"); size = struct.unpack_from("<Q", values, position)[0]; position += 8
                if compressed == 0xFFFFFFFF:
                    require(position+8 <= len(values), "Short ZIP64 size"); compressed = struct.unpack_from("<Q", values, position)[0]; position += 8
                require(position == len(values), "Unexpected local ZIP64 fields")
            else: require(1 not in extra, "Unexpected ZIP64 extra")
            if flags & 8:
                require(crc in (0, r["crc"]) and compressed in (0, r["compressed"]) and size in (0, r["size"]), "Local descriptor placeholders mismatch")
            else: require((crc, compressed, size) == (r["crc"], r["compressed"], r["size"]), "Local/central sizes/CRC mismatch")
            cursor += 30 + nl + el + r["compressed"]; require(cursor <= cd_offset, "Local payload overflow")
            if flags & 8:
                signature = read(cursor, 4, cd_offset) == b"PK\x07\x08"
                # A CRC equal to the optional signature is ambiguous; signed forms
                # are required in that exceptional case.
                if signature: cursor += 4
                fmt = "<IQQ" if zip64 else "<III"; width = struct.calcsize(fmt)
                require(struct.unpack(fmt, read(cursor, width, cd_offset)) == (r["crc"], r["compressed"], r["size"]), "Invalid data descriptor")
                cursor += width
        require(cursor == cd_offset, "Hidden ZIP data before directory")
        return records
