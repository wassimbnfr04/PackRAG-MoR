"""Serialized pinned llama.cpp desktop backend using its actual GGUF tokenizer.

The server is owned by the smoke launcher. Android will use JNI, not this HTTP API.
Raw reasoning exists only in the returned in-memory buffer; callers persist final
validated text and token/timing metadata only.
"""
from __future__ import annotations

import json
import threading
import time
import urllib.request
from pathlib import Path

from transformers.utils.chat_template_utils import _compile_jinja_template

from .config import LOCK, RuntimeContractError, file_sha, verify_file
from .generator_api import Generated


class LlamaBackend:
    def __init__(self, port: int, model: Path, template: Path, binary: Path):
        verify_file(model, LOCK["generator"]["sha256"])
        verify_file(template, LOCK["generator"]["chat_template_sha256"])
        expected_binary = LOCK["generator"].get("desktop_binary_sha256")
        if not expected_binary:
            raise RuntimeContractError("Desktop runtime binary is not hash-pinned")
        verify_file(binary, expected_binary)
        self.url = f"http://127.0.0.1:{port}"
        self.http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self._mutex = threading.Lock()
        self.template = _compile_jinja_template(template.read_text(encoding="utf-8"))
        self.metadata = dict(model_sha256=file_sha(model), template_sha256=file_sha(template),
                             runtime_binary_sha256=file_sha(binary),
                             llama_cpp_commit=LOCK["generator"]["llama_cpp_commit"],
                             quantization="QAD-Q4_0", backend="llama.cpp-cpu-wsl-desktop")

    def request(self, endpoint: str, body: dict | None = None) -> dict:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = urllib.request.Request(self.url + endpoint, data=data,
                                         headers={"Content-Type": "application/json"})
        with self.http.open(request, timeout=600) as response:
            return json.load(response)

    def tokenize(self, text: str, *, add_special: bool) -> list[int]:
        result = self.request("/tokenize", dict(content=text, add_special=add_special, parse_special=True))
        tokens = result["tokens"]
        if any(type(token) is not int for token in tokens):
            raise RuntimeContractError("Unexpected tokenizer response")
        return tokens

    def render_tokens(self, system: str, user: str) -> list[int]:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        rendered = self.template.render(messages=messages, bos_token="<|startoftext|>",
                                        eos_token="<|im_end|>", add_generation_prompt=True,
                                        tools=None, raise_exception=lambda text: (_ for _ in ()).throw(RuntimeContractError(text)))
        if not rendered.startswith("<|startoftext|>") or rendered.count("<|startoftext|>") != 1:
            raise RuntimeContractError("Template must have exactly one BOS")
        applied = self.request("/apply-template", dict(messages=messages, add_generation_prompt=True))["prompt"]
        server_full = applied if applied.startswith("<|startoftext|>") else "<|startoftext|>" + applied
        if rendered != server_full or not rendered.endswith("<|im_start|>assistant\n<think>"):
            raise RuntimeContractError("Official/server template mismatch")
        full_tokens = self.tokenize(rendered, add_special=False)
        body_tokens = self.tokenize(rendered.removeprefix("<|startoftext|>"), add_special=True)
        if full_tokens != body_tokens:
            raise RuntimeContractError("BOS/tokenizer parity mismatch")
        return full_tokens

    def generate(self, prompt) -> Generated:
        with self._mutex:
            start = time.perf_counter()
            result = self.request("/completion", dict(
                prompt=list(prompt.tokens), n_predict=prompt.max_new_tokens, stream=False,
                samplers=["temperature"], temperature=0, top_p=1, seed=0,
                repeat_penalty=1, cache_prompt=False, return_tokens=True,
            ))
            tokens = tuple(result.get("tokens", ()))
            # llama-server's `truncated` describes INPUT truncation. Output cap
            # exhaustion is `stop_type=limit`; mirror Android NativeEmission.stop=1.
            stop_type = result.get("stop_type")
            if stop_type not in ("eos", "limit"):
                raise RuntimeContractError("GENERATION_UNUSABLE")
            output_truncated = bool(result.get("truncated", False)) or stop_type == "limit"
            timing = dict(result.get("timings", {}))
            closing = self.tokenize("</think>", add_special=False)
            if len(closing) != 1:
                raise RuntimeContractError("Unexpected reasoning closing token")
            partition = tokens.index(closing[0]) + 1 if closing[0] in tokens else None
            timing.update(host_generation_wall_ms=(time.perf_counter() - start) * 1000,
                          emitted_token_count=len(tokens), reasoning_token_count=partition,
                          final_and_terminal_token_count=len(tokens) - partition if partition is not None else None,
                          token_partition_method="actual_emitted_ids", ttft_ms=None,
                          stop_type=stop_type, output_truncated=output_truncated,
                          ttft_measurement="not_measured_nonstreaming")
            return Generated(result["content"], output_truncated, tokens, timing)
