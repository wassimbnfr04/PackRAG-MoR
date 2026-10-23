"""Copied signed source assertions; no external permission/review/entailment claim."""
from .config import RuntimeContractError

def source_attribution(row):
    allowed=row.get('redistribution_allowed')
    if allowed is not None and (type(allowed) not in (int,bool) or allowed not in (0,1)):
        raise RuntimeContractError('INVALID_SOURCE_ATTRIBUTION')
    return dict(canonical_uri=row.get('canonical_uri'),retrieved_at=row.get('retrieved_at'),license=row.get('license'),
        redistribution_allowed=None if allowed is None else bool(allowed),source_type=row.get('source_type'),
        snapshot_path=row.get('snapshot_path'),notes=row.get('notes'))

def source_location(row):
    return dict(chunk_title=row.get('title'),section=row.get('section'),page_start=row.get('page_start'),
        page_end=row.get('page_end'),character_start=row.get('character_start'),character_end=row.get('character_end'))
