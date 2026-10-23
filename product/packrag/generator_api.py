"""Desktop generator/tokenizer boundary; local server lifecycle belongs to its owner."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, TYPE_CHECKING, runtime_checkable
if TYPE_CHECKING:
    from .prompt import PreparedPrompt

@dataclass(frozen=True)
class Generated:
    buffer: str = field(repr=False)
    truncated: bool
    emitted_tokens: tuple[int, ...]
    timings: dict

@runtime_checkable
class GeneratorBackend(Protocol):
    metadata: dict
    def tokenize(self, text: str, *, add_special: bool) -> list[int]: ...
    def render_tokens(self, system: str, user: str) -> list[int]: ...
    def generate(self, prompt: PreparedPrompt) -> Generated: ...
