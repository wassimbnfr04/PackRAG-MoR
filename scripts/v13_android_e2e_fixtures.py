"""Versioned bounded smoke inputs; not release gold or PackBench cases."""
import argparse
import json
from pathlib import Path
from product.packrag.config import file_sha

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    run = args.run.resolve()
    assert run.is_relative_to(ROOT)
    run.mkdir(parents=True, exist_ok=False)
    source = ROOT / "gates/g0/g0_v1.jsonl"
    original = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()][:10]
    facts = ["74", "600", "LiFePO4", "three", "18", "20%", "8", "12", "80", "99.999%"]
    value = dict(purpose="M2_DEVELOPMENT_SMOKE_NOT_FULL_G0_OR_SEMANTIC_REVIEW_OR_PACKBENCH", source_sha256=file_sha(source),
                 criterion="Same bounded expected-fact substring check as M1, plus structural citation/source/state assertions. Full original expected facts are retained separately.",
                 supported=[dict(case_id=case["case_id"], question=case["question"], original_expected_facts=case["expected_facts"],
                                 smoke_expected_fact=fact) for case, fact in zip(original, facts, strict=True)])
    output = run / "e2e-cases.json"
    output.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    target = ROOT / "product/android/app/src/androidTest/assets/e2e-cases.json"
    assert not target.exists(), "Do not silently replace fixture inputs"
    target.write_bytes(output.read_bytes())
    (run / "output-hash.json").write_text(json.dumps({"sha256": file_sha(output)}, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
