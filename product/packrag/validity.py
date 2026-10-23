"""Signed source/chunk interval provenance; no inferred dates or freshness rule."""


def validity_provenance(row: dict) -> dict:
    source_start, source_end = row["source_from"], row["source_until"]
    chunk_start, chunk_end = row["effective_from"], row["effective_until_excl"]
    start = max((v for v in (source_start, chunk_start) if v is not None), default=None)
    end = min((v for v in (source_end, chunk_end) if v is not None), default=None)
    return dict(source_from=source_start, source_until_excl=source_end,
                chunk_from=chunk_start, chunk_until_excl=chunk_end,
                effective_from=start, effective_until_excl=end,
                source_start_unknown=source_start is None, source_end_unknown=source_end is None,
                chunk_start_inherits=chunk_start is None, chunk_end_inherits=chunk_end is None,
                empty_intersection=start is not None and end is not None and start >= end,
                jurisdiction=row["jurisdiction"], legal_status=row["legal_status"])
