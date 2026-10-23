"""Versioned generation only; mobile-v1 retrieval and the literal baseline remain.

Quoted output is actual model emission, never a reconstructed accepted answer.
Source identity/relevance/sufficiency are separate from literal unit admission.
"""
from dataclasses import dataclass
import json
from .config import ROOT, RuntimeContractError, verify_file

QUOTE_CONFIG_SHA = 'dae71e602caa7f10e9030f4a19e21b44d513067ebccbc9ccee600b996965225d'
_path = ROOT / 'config/generation-profile-quotes-v1.json'
verify_file(_path, QUOTE_CONFIG_SHA)
_data = json.loads(_path.read_text(encoding='utf8'))
assert (_data['schema_version'], _data['compatible_retrieval_profile'],
        _data['context_tokens'], _data['generated_tokens_cap'],
        _data['prefill_tokens_cap'], _data['max_evidence_tokens_cap'],
        _data['max_evidence_chunks'], _data['max_quote_units'],
        _data['max_output_lines']) == (1, 'mobile-v1', 3072, 1536, 1536, 1200, 4, 64, 4)


@dataclass(frozen=True)
class GenerationPolicy:
    profile_id: str
    context: int
    generated: int
    suffix: str = ''
    quoted: bool = False

    def system(self, baseline: str) -> str:
        return baseline + ('\n' + self.suffix if self.quoted else '')

    def runtime_profile(self, baseline: dict) -> dict:
        result = dict(baseline)
        if self.quoted:
            result.update(profile_id=self.profile_id, context_tokens=self.context,
                          generated_tokens_cap=self.generated,
                          compatible_retrieval_profile='mobile-v1',
                          generation_profile_sha256=QUOTE_CONFIG_SHA)
        return result


BASELINE = GenerationPolicy('mobile-v1', 2048, 512)
QUOTES = GenerationPolicy(_data['profile_id'], 3072, 1536, _data['system_suffix'], True)


def quote_units(texts) -> tuple[str, ...]:
    texts = tuple(texts)
    if not 1 <= len(texts) <= 4:
        raise RuntimeContractError('INPUT_TOO_LONG')
    units = tuple(dict.fromkeys(line.strip() + f' [S{i}]'
                  for i, text in enumerate(texts, 1)
                  for line in text.splitlines() if line.strip()))
    if not 1 <= len(units) <= 64:
        raise RuntimeContractError('INPUT_TOO_LONG')
    return units


def quote_grammar(units) -> str:
    units = tuple(units)
    if not 1 <= len(units) <= 64:
        raise RuntimeContractError('INPUT_TOO_LONG')
    grammar = '\n'.join([
        'root ::= "</think>" pad ("INSUFFICIENT_EVIDENCE" | "1. " line (sep "2. " line (sep "3. " line (sep "4. " line)?)?)?) pad',
        'line ::= ' + ' | '.join(json.dumps(unit, ensure_ascii=False) for unit in units),
        r'pad ::= ("\n" | "\n\n")?', r'sep ::= "\n" | "\n\n"']) + '\n'
    if len(grammar.encode('utf8')) > 128 * 1024:
        raise RuntimeContractError('INPUT_TOO_LONG')
    return grammar


def matches_quote_units(final: str, units) -> bool:
    allowed = frozenset(units)
    lines = tuple(line.strip() for line in final.splitlines() if line.strip())
    if not 1 <= len(lines) <= 4:
        return False
    selected = []
    for i, line in enumerate(lines, 1):
        prefix = f'{i}. '
        if not line.startswith(prefix) or line[len(prefix):] not in allowed:
            return False
        selected.append(line[len(prefix):])
    return len(set(selected)) == len(selected)
