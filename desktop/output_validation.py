"""Syntax validation only; citation validity does not prove semantic support."""
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class ValidatedAnswer:
    status: str
    display_text: str | None
    citations: tuple[str,...]

def validate_answer(text: str, supplied_ids: set[str]) -> ValidatedAnswer:
    if text == 'INSUFFICIENT_EVIDENCE':
        return ValidatedAnswer('INSUFFICIENT_EVIDENCE', None, ())
    ids = tuple(dict.fromkeys(re.findall(r'\[(S\d+)\]', text)))
    if not ids or any(i not in supplied_ids for i in ids):
        return ValidatedAnswer('UNGROUNDED', None, ids)
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if any(not re.search(r'\[S\d+\]', p) for p in paragraphs):
        return ValidatedAnswer('UNCITED_PARAGRAPH', None, ids)
    if re.search(r'</?(?:SYSTEM|ANSWER|QUESTION|CONTEXT|VERIFIED_EVIDENCE)\b', text):
        return ValidatedAnswer('INVALID_FORMAT', None, ids)
    return ValidatedAnswer('ACCEPTED_SYNTAX_ONLY', text, ids)

def identifier_admission(eligible_hits: list[str]) -> str:
    if len(set(eligible_hits)) > 1: return 'AMBIGUOUS_IDENTIFIER'
    return 'REQUIRES_FINAL_EVIDENCE_ADMISSION' if eligible_hits else 'NO_IDENTIFIER_HIT'
