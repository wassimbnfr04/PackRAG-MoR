import hashlib
import json
import re
import unicodedata
from pathlib import Path

from product.packrag.query_unicode import VERSION, lowercase, nfkc, normalize
from scripts.v13_query_unicode import generate

ROOT = Path(__file__).resolve().parents[2]
INPUTS = ROOT / "artifacts/v1.3/m4/unicode15-inputs-0001"


def test_official_unicode15_normalization_conformance():
    assert VERSION == unicodedata.unidata_version == "15.0.0"
    count = 0
    for line in (ROOT / "product/tests/unicode15/NormalizationTest.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("@"):
            continue
        columns = [''.join(chr(int(p, 16)) for p in field.split()) for field in line.split(";")[:5]]
        for column in columns:
            assert nfkc(column) == columns[3], (count, column.encode("unicode_escape"))
        count += 1
    assert count == 19074


def test_every_scalar_and_context_against_pinned_unicode15_engine():
    assert unicodedata.unidata_version == "15.0.0"
    for point in range(0x110000):
        if 0xD800 <= point <= 0xDFFF:
            continue
        char = chr(point)
        assert nfkc(char) == unicodedata.normalize("NFKC", char), hex(point)
        assert lowercase(char) == char.lower(), hex(point)
    cases = json.loads((ROOT / "product/tests/query-unicode-cases.json").read_text())
    for case in cases["cases"]:
        raw = case["raw"]
        expected = ' '.join(re.sub("[\u064b-\u065f\u0670]", "", unicodedata.normalize("NFKC", raw).replace("\u0640", "")).lower().split())
        assert normalize(raw) == expected == case["normalized"]


def test_official_unicode_data_properties_and_reproducible_tables():
    for line in (INPUTS / "UnicodeData.txt").read_text(encoding="utf-8").splitlines():
        fields = line.split(";")
        point = int(fields[0], 16)
        char = chr(point)
        assert unicodedata.combining(char) == int(fields[3])
        assert unicodedata.decomposition(char) == fields[5]
        assert unicodedata.category(char) == fields[2]
    generated_json, generated_kotlin = generate(INPUTS)
    assert (ROOT / "product/config/query-unicode15.json").read_bytes() == generated_json
    assert (ROOT / "product/android/core-model/src/main/java/org/packrag/model/QueryUnicodeData.kt").read_bytes() == generated_kotlin
    for destination in (ROOT / "product/tests/unicode15/NormalizationTest.txt", ROOT / "product/android/app/src/androidTest/assets/unicode15/NormalizationTest.txt"):
        assert hashlib.sha256(destination.read_bytes()).digest() == hashlib.sha256((INPUTS / "NormalizationTest.txt").read_bytes()).digest()
