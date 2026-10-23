"""Buffered structural validation. Citation syntax alone does not prove factual support."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ValidatedOutput:
    state: str
    text: str | None
    citations: tuple[str, ...] = ()
    reason: str | None = None


def validate_output(buffer: str, supplied: set[str], *, truncated: bool = False) -> ValidatedOutput:
    if truncated or buffer.count("</think>") != 1:
        return ValidatedOutput("GENERATION_UNUSABLE", None, reason="unfinished_reasoning_or_truncated")
    final = buffer.split("</think>", 1)[1].strip()
    if not final or "<think>" in final or "<|" in final:
        return ValidatedOutput("GENERATION_UNUSABLE", None, reason="empty_or_malformed_final")
    if final == "INSUFFICIENT_EVIDENCE":
        return ValidatedOutput("INSUFFICIENT_EVIDENCE", None)
    citations = re.findall(r"\[S[^\]\n]*\]", final)
    ids = tuple(dict.fromkeys(value[1:-1] for value in citations))
    if not ids or any(not re.fullmatch(r"S[1-9]\d*", value) or value not in supplied for value in ids):
        return ValidatedOutput("OUTPUT_REJECTED", None, reason="missing_or_unknown_citation")
    if "[S" in re.sub(r"\[S[1-9]\d*\]", "", final):
        return ValidatedOutput("OUTPUT_REJECTED", None, reason="malformed_citation")
    # Conservative structural rule: each nonempty paragraph must contain a supplied
    # citation. No automated assertion of semantic entailment or support is made.
    if any(not re.search(r"\[S[1-9]\d*\]", paragraph) for paragraph in re.split(r"\n\s*\n", final)):
        return ValidatedOutput("OUTPUT_REJECTED", None, reason="uncited_paragraph")
    return ValidatedOutput("ANSWER_ACCEPTED", final, ids)
