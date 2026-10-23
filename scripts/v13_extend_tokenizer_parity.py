"""New versioned references for the concrete Android Unicode-class compatibility repair."""
import json
from pathlib import Path

from tokenizers import Tokenizer
from product.packrag.config import file_sha

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / "artifacts/v1.3/m2/parity-reference-0001/parity-reference.json"
    output = ROOT / "artifacts/v1.3/m2/parity-reference-0002"
    output.mkdir(exist_ok=False)
    record = json.loads(source.read_text(encoding="utf-8"))
    tokenizer = Tokenizer.from_file(str(ROOT / "models/v1.3/granite/tokenizer.json"))
    tokenizer.no_truncation()
    extra = ["a\u00a0b", "a\u0085b", "a\u2003b", "a\u2028b", "a\u2029b", "a\u3000b",
             "a\u202fb\u2009c", " \u00a0\u2003\t\nabc"]
    record["tokenizer_cases"].extend(dict(id=f"UNICODE-SPACE-{index:02}", text=text,
                                         ids=tokenizer.encode(text, add_special_tokens=True).ids)
                                     for index, text in enumerate(extra))
    record["previous_reference_sha256"] = file_sha(source)
    record["extension_reason"] = "Android ICU Unicode classes are always enabled; verify whitespace behavior on both engines without changing the pinned regex."
    (output / "parity-reference.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("44 tokenizer cases frozen; prior references unchanged.")


if __name__ == "__main__":
    main()
