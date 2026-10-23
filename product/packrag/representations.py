"""Authenticated generator-language rendering, separate from canonical evidence.

Metadata is a publisher assertion, not proof that a human actually reviewed it.
Release source/review evidence is independently required. Never translate here.
"""
import hashlib
from dataclasses import dataclass
from .config import RuntimeContractError
from .temporal import date_or_timestamp
from .languages import valid_tag

@dataclass(frozen=True)
class GeneratorRepresentation:
    text: str
    language: str
    text_sha256: str
    derivation_method: str
    derivation_source: str | None
    reviewer_id: str | None
    reviewed_at: str | None
    canonical_language: str
    canonical_text_sha256: str

def english(language):return type(language) is str and valid_tag(language) and language.lower().split('-')[0]=='en'
def nonblank(value):return type(value) is str and bool(value.strip())

def select_representation(chunk, derived):
    canonical=chunk['canonical_text'];canonical_hash=chunk['text_sha256'];language=chunk['language']
    if not valid_tag(language):raise RuntimeContractError('INVALID_GENERATOR_PROVENANCE')
    if hashlib.sha256(canonical.encode('utf-8')).hexdigest()!=canonical_hash:
        raise RuntimeContractError('GENERATOR_REPRESENTATION_HASH_MISMATCH')
    if not nonblank(canonical):raise RuntimeContractError('INVALID_GENERATOR_PROVENANCE')
    if english(language):
        return GeneratorRepresentation(canonical,language,canonical_hash,'canonical',None,None,None,language,canonical_hash)
    eligible=[row for row in derived if row['purpose']=='generator' and english(row['language'])
              and row['derivation_method'] in ('official_translation','human_reviewed_translation')]
    preferred=[row for row in eligible if row['language'].lower()=='en']
    choices=preferred or eligible
    if not choices:raise RuntimeContractError('NO_ELIGIBLE_GENERATOR_REPRESENTATION')
    if len(choices)!=1:raise RuntimeContractError('AMBIGUOUS_GENERATOR_REPRESENTATION')
    row=choices[0]
    if not nonblank(row['text']) or not nonblank(row['derivation_source']):
        raise RuntimeContractError('INVALID_GENERATOR_PROVENANCE')
    if row['derivation_method']=='human_reviewed_translation':
        if not nonblank(row['reviewer_id']) or not nonblank(row['reviewed_at']):raise RuntimeContractError('INVALID_GENERATOR_PROVENANCE')
        try:date_or_timestamp(row['reviewed_at'])
        except (TypeError,ValueError):raise RuntimeContractError('INVALID_GENERATOR_PROVENANCE') from None
    if hashlib.sha256(row['text'].encode('utf-8')).hexdigest()!=row['text_sha256']:
        raise RuntimeContractError('GENERATOR_REPRESENTATION_HASH_MISMATCH')
    return GeneratorRepresentation(row['text'],row['language'],row['text_sha256'],row['derivation_method'],
        row['derivation_source'],row['reviewer_id'],row['reviewed_at'],language,canonical_hash)
