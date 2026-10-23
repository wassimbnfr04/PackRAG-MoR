"""Independent official PyTorch/CLS versus product FP32 ONNX encoder parity."""
import argparse
import json
import platform
from pathlib import Path

import numpy as np
import onnxruntime
import torch
import transformers
from transformers import AutoModel, AutoTokenizer

from product.packrag.config import LOCK, file_sha
from product.packrag.embedding import GraniteEncoder

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    args.run.mkdir(parents=True, exist_ok=False)
    path = ROOT / "models/v1.3/granite"
    inputs = ["Aster-9 operating temperature", "Quelle est la durée du congé annuel ?",
              "ما هي ساعات العمل؟", "ch7al sa3a dyal lkhedma"]
    model = AutoModel.from_pretrained(path, local_files_only=True, dtype=torch.float32, attn_implementation="sdpa")
    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
    model.eval()
    torch.set_num_threads(4)
    encoder = GraniteEncoder(path)
    records = []
    for text in inputs:
        tokens = tokenizer(text, return_tensors="pt", truncation=False)
        with torch.no_grad():
            vector = model(**tokens).last_hidden_state[0, 0].float().numpy()
        vector /= np.linalg.norm(vector)
        onnx = encoder.encode(text)
        maximum = float(np.max(np.abs(vector - onnx)))
        cosine = float(np.dot(vector, onnx))
        records.append(dict(text=text, input_ids=tokens["input_ids"][0].tolist(),
                            max_abs_error=maximum, cosine=cosine, passed=maximum <= 1e-4 and cosine >= .99999,
                            torch_vector=vector.tolist(), onnx_vector=onnx.tolist()))
    result = dict(status="PASS" if all(row["passed"] for row in records) else "FAIL", cases=records,
                  revision=LOCK["embedder"]["revision"], pooling="CLS then L2", dtype="float32",
                  limits=dict(max_abs_error=1e-4, minimum_cosine=.99999),
                  model_sha256=file_sha(path / "model.safetensors"), onnx_sha256=file_sha(path / "onnx/model.onnx"),
                  versions=dict(torch=torch.__version__, transformers=transformers.__version__,
                                onnxruntime=onnxruntime.__version__, python=platform.python_version()),
                  purpose="ENCODER_NUMERIC_PARITY_NOT_DARIJA_RETRIEVAL_ACCEPTANCE")
    (args.run / "encoder-parity.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(result["status"], [(row["max_abs_error"], row["cosine"]) for row in records], flush=True)
    assert result["status"] == "PASS", "Encoder numeric parity failed"


if __name__ == "__main__":
    main()
