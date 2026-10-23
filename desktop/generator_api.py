"""Buffered generator boundary. Retrieval and KPack never inspect model internals."""
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class GenerationResult:
    text: str
    prompt_tokens: int
    generated_tokens: int
    time_to_first_token_ms: float
    total_latency_ms: float
    average_tokens_per_second: float
    model_hash: str
    backend_name: str
    quantization: str
    input_ids: list[int]
    generated_ids: list[int]

class GeneratorBackend(Protocol):
    def load(self, model_path: str) -> dict: ...
    def generate(self, prompt: str, max_new_tokens: int=128,
                 temperature: float=0.0, top_p: float=1.0,
                 stop_strings: tuple[str,...]=()) -> GenerationResult: ...
    def close(self) -> None: ...
