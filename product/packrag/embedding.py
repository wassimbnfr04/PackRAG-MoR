"""One hash-pinned CPU ONNX query/document encoder; no network access."""
from __future__ import annotations

import threading
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from .config import LOCK, RuntimeContractError, embedding_profile, verify_file


class GraniteEncoder:
    def __init__(self, assets: Path, threads: int = 4):
        self.profile = embedding_profile()
        for name, expected in LOCK["embedder"]["asset_sha256"].items():
            verify_file(assets / name, expected)
        self.tokenizer = Tokenizer.from_file(str(assets / "tokenizer.json"))
        self.tokenizer.no_truncation()
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(
            str(assets / "onnx/model.onnx"), options, providers=["CPUExecutionProvider"]
        )
        self.inputs = {item.name for item in self.session.get_inputs()}
        if not {"input_ids", "attention_mask"} <= self.inputs:
            raise RuntimeContractError("Unsupported ONNX input contract")
        self._lock = threading.Lock()

    def encode(self, text: str) -> np.ndarray:
        with self._lock:
            encoded = self.tokenizer.encode(text, add_special_tokens=True)
            if len(encoded.ids) > self.profile["max_input_length"]:
                raise RuntimeContractError("EMBEDDING_INPUT_TOO_LONG")
            ids = np.asarray([encoded.ids], dtype=np.int64)
            feeds = {"input_ids": ids, "attention_mask": np.ones_like(ids)}
            if "token_type_ids" in self.inputs:
                feeds["token_type_ids"] = np.asarray([encoded.type_ids], dtype=np.int64)
            if set(feeds) != self.inputs:
                raise RuntimeContractError("Unsupported ONNX input contract")
            outputs = self.session.run(None, feeds)
            names = [item.name for item in self.session.get_outputs()]
            tensors = dict(zip(names, outputs, strict=True))
            if "last_hidden_state" in tensors:
                vector = tensors["last_hidden_state"][0, 0]
            elif "sentence_embedding" in tensors:
                vector = tensors["sentence_embedding"][0]
            else:
                raise RuntimeContractError("Unsupported ONNX pooling contract")
            vector = np.asarray(vector, dtype=np.float32)
            norm = float(np.linalg.norm(vector))
            if vector.shape != (384,) or not np.isfinite(vector).all() or norm <= 0:
                raise RuntimeContractError("Invalid encoder output")
            return vector / norm


def document_input(title: str, section: str, context_prefix: str, text: str) -> str:
    return "\n".join((title, section, context_prefix, text))
