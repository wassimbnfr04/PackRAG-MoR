"""Strict product manifest semantics, applied only after exact-byte authentication."""
import math
import re

from kpack_builder.core import PackError, canonical
from .archive import safe_path, allowed_media_type
from .languages import valid_tag
from .temporal import iso_date, utc_timestamp
from .errors import require
from .portable_names import fold


def version(value):
    match = re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?", value)
    require(match is not None, "Invalid SemVer")
    pre = match[4].split(".") if match[4] else []
    require(not any(p.isdigit() and len(p) > 1 and p.startswith("0") for p in pre), "Leading zero in prerelease")
    return tuple(map(int, match.group(1, 2, 3))), pre


def compare_versions(a, b):
    ac, ap = version(a); bc, bp = version(b)
    def compare(x, y): return (x > y) - (x < y)
    if ac != bc: return compare(ac, bc)
    if not ap or not bp: return compare(not ap, not bp)
    for x, y in zip(ap, bp):
        xn, yn = x.isdigit(), y.isdigit()
        c = compare(int(x), int(y)) if xn and yn else compare(not xn, not yn) if xn != yn else compare(x, y)
        if c: return c
    return compare(len(ap), len(bp))


def validate_manifest(m, profile, developer_mode):
    def fields(v, required, optional=()):
        require(type(v) is dict and set(required) <= set(v) <= set(required) | set(optional), "Manifest fields mismatch")
    def text(v, key):
        item = v[key]; require(type(item) is str and bool(item.strip()), "Invalid string: " + key); return item
    def integer(v, key, maximum):
        item = v[key]; require(type(item) is int and 0 <= item <= maximum, "Invalid integer: " + key); return item
    def array(v, key, nonempty):
        item = v[key]
        require(type(item) is list and len(item) <= 5000 and all(type(i) is str and i.strip() for i in item))
        require((not nonempty or item) and len(set(item)) == len(item)); return item
    def hash_(v): require(re.fullmatch(r"[0-9a-f]{64}", v))
    try:
        fields(m, ("schema_version", "pack_id", "name", "version", "release_timestamp", "publisher", "languages", "jurisdictions", "domain", "freshness", "embedding_profile", "compatible_retrieval_profile", "generator_compatibility", "counts", "calibration", "build", "files"))
        require(text(m, "schema_version") == "1.0")
        pack_id = text(m, "pack_id")
        require(re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)+", pack_id) and len(pack_id.encode("utf-8")) <= 255, "Pack ID exceeds portable installation component")
        text(m, "name"); text(m, "domain")
        pack_version = text(m, "version")
        require(len(pack_version.encode("utf-8")) <= 255, "Version exceeds portable installation component")
        version(pack_version)
        release = text(m, "release_timestamp")
        utc_timestamp(release)
        p = m["publisher"]; fields(p, ("name", "key_id")); text(p, "name")
        require(re.fullmatch(r"ed25519:[0-9a-f]{64}", text(p, "key_id")))
        languages = array(m, "languages", True)
        require(all(valid_tag(i) for i in languages) and len(set(i.lower() for i in languages)) == len(languages))
        require(all(re.fullmatch(r"[A-Z]{2}(?:-[A-Z0-9]{1,3})?", i) for i in array(m, "jurisdictions", False)))
        f = m["freshness"]; fields(f, ("update_check_after", "stale_behavior")); iso_date(text(f, "update_check_after"))
        require(text(f, "stale_behavior") == "warn-and-continue")
        require(type(m["embedding_profile"]) is dict and canonical(m["embedding_profile"]) == canonical(profile))
        require(text(m, "compatible_retrieval_profile") == "mobile-v1")
        g = m["generator_compatibility"]; fields(g, ("core_api", "preferred_generator_language", "neural_cache_required"))
        require(text(g, "core_api") == "1.x" and text(g, "preferred_generator_language") == "en" and g["neural_cache_required"] is False)
        counts = m["counts"]; fields(counts, ("sources", "chunks", "relations"))
        for key in counts: integer(counts, key, 2147483647)
        c = m["calibration"]
        metrics = ("min_agreed_dense_cosine", "min_dense_only_cosine", "precision", "recall")
        fields(c, ("dataset_sha256", "method", *metrics), ("status",))
        require(text(c, "method") == "candidate-relevance-v1.3")
        status = text(c, "status") if "status" in c else "CALIBRATED"
        require(status in ("UNCALIBRATED", "CALIBRATED"))
        require(developer_mode or status != "UNCALIBRATED", "Uncalibrated pack requires developer mode")
        if status == "UNCALIBRATED": require(all(c[key] is None for key in (*metrics, "dataset_sha256")))
        else:
            hash_(text(c, "dataset_sha256"))
            for key in metrics:
                v = c[key]
                require(type(v) in (int, float) and math.isfinite(v) and (-1 if key.endswith("cosine") else 0) <= v <= 1)
        b = m["build"]; fields(b, ("builder_version", "normalizer_version", "chunker_version", "source_manifest_sha256"), ("build_input_sha256",))
        for key in ("builder_version", "normalizer_version", "chunker_version"): text(b, key)
        for key in ("source_manifest_sha256", "build_input_sha256"):
            if key in b: hash_(text(b, key))
        files = m["files"]; require(type(files) is list and 2 <= len(files) <= 4998)
        names, total = [], 0
        for f in files:
            fields(f, ("path", "sha256", "bytes", "media_type", "required"))
            path = text(f, "path"); safe_path(path); require(path not in ("manifest.json", "manifest.sig")); names.append(path)
            hash_(text(f, "sha256")); total += integer(f, "bytes", 256 * 1024 * 1024)
            require(type(f["required"]) is bool)
            require(re.fullmatch(r"[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+", text(f, "media_type")))
            allowed_media_type(path, f["media_type"])
            if path in ("knowledge.sqlite", "dense.kdx"): require(f["required"] is True)
        require(total <= 512 * 1024 * 1024 and names == sorted(names) and len(set(fold(i) for i in names)) == len(names))
        require({"knowledge.sqlite", "dense.kdx"} <= set(names))
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        if isinstance(error, PackError): raise
        raise PackError("Invalid product manifest: " + str(error)) from error
