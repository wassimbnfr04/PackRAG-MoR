import json
from pathlib import Path

_table=json.loads((Path(__file__).resolve().parents[1]/"config/portable-names.json").read_text(encoding="utf-8"))
UNICODE_VERSION=_table["unicode_version"]
_mappings={int(key):value for key,value in _table["mappings"].items()}


def fold(text): return "".join(_mappings.get(ord(c),c) for c in text)
