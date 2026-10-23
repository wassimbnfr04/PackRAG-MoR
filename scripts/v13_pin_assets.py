"""Freeze acquired, hash-verified assets into the product lock; no invented identities."""
import json
from pathlib import Path

from product.packrag.config import file_sha

ROOT = Path(__file__).resolve().parents[1]


def main():
    record = json.loads((ROOT / "artifacts/v1.3/m0/assets/granite-assets.json").read_text(encoding="utf-8"))
    files = {item["path"]: item["sha256"] for item in record["files"]}
    for name, expected in files.items():
        assert file_sha(ROOT / "models/v1.3/granite" / name) == expected
    path = ROOT / "product/config/toolchain.lock.json"
    lock = json.loads(path.read_text(encoding="utf-8"))
    assert record["revision"] == lock["embedder"]["revision"]
    generator = lock["generator"]
    assert file_sha(ROOT / generator["artifact"]) == generator["sha256"]
    candidate = ROOT / "04_LFM25_26B_Candidate_Evidence"
    assert file_sha(candidate / "model/chat_template.jinja") == generator["chat_template_sha256"]
    assert file_sha(candidate / "model/LICENSE") == generator["license_sha256"]
    generator["desktop_binary_sha256"] = file_sha(candidate / "runtime/wsl-build/bin/llama-server")
    generator["desktop_backend"] = "CPU_WSL"
    embedder = lock["embedder"]
    embedder["asset_sha256"] = {name: value for name, value in files.items()
                               if name not in ("README.md", "model.safetensors")}
    embedder["asset_hash_status"] = "VERIFIED"
    embedder["pack_profile"] = dict(
        profile_id=embedder["profile_id"], model_id=embedder["model_id"],
        model_revision=embedder["revision"], model_sha256=files["model.safetensors"],
        onnx_sha256=files["onnx/model.onnx"],
        tokenizer_hashes={name: files[name] for name in ("tokenizer.json", "tokenizer_config.json")},
        dimension=384, dtype="float32", normalized=True, metric="cosine", runtime=embedder["runtime"],
        pooling=json.loads((ROOT / "models/v1.3/granite/1_Pooling/config.json").read_text(encoding="utf-8")),
        max_input_length=512,
        input_construction="title + newline + section_or_article + newline + search_safe_context_prefix + newline + canonical_or_verified_english_text",
    )
    lock["status"] = "ASSET_IDENTITIES_VERIFIED_NOT_RELEASE_ACCEPTANCE"
    path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print("Verified LFM/template/license/runtime and pinned Granite assets; product lock updated.")


if __name__ == "__main__":
    main()
