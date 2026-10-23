"""Authenticated metadata exposure only; no authority preference or graph expansion."""


def source_metadata(pack, row: dict) -> dict:
    return dict(authority_rank=row["authority_rank"], document_version=row["document_version"],
                issued_at=row["issued_at"], article=row["article"],
                publisher_key_id=pack.manifest["publisher"]["key_id"],
                relations=[dict(relation) for relation in pack.relations
                           if row["chunk_id"] in (relation["from_chunk_id"], relation["to_chunk_id"])])
