"""Owned evidence values: no live reader, array, manifest or nested dict escapes."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import math

from .config import PROFILE, RuntimeContractError
from .conflicts import ConflictDecision
from .representations import GeneratorRepresentation, select_representation
from .source_metadata import source_metadata
from .source_attribution import source_attribution


@dataclass(frozen=True)
class OwnedMap(Mapping):
    entries: tuple[tuple[str, object], ...]

    def __getitem__(self,key):
        for name,value in self.entries:
            if name==key:return value
        raise KeyError(key)

    def __iter__(self):return (name for name,_ in self.entries)
    def __len__(self):return len(self.entries)


def own(value):
    if isinstance(value,Mapping):
        if any(type(key) is not str for key in value):raise RuntimeContractError('INVALID_EVIDENCE_VALUE')
        return OwnedMap(tuple((key,own(value[key])) for key in sorted(value)))
    if isinstance(value,(list,tuple)):return tuple(own(item) for item in value)
    if value is None or type(value) in (str,int,bool):return value
    if type(value) is float and math.isfinite(value):return value
    raise RuntimeContractError('INVALID_EVIDENCE_VALUE')


def export(value):
    """Fresh JSON values for diagnostics; never returns a backing collection."""
    if isinstance(value,Mapping):return {key:export(value[key]) for key in value}
    if isinstance(value,tuple):return [export(item) for item in value]
    return value


def own_conflict(value):
    return ConflictDecision(tuple(value.members),value.state,value.reason,value.preferred,
        tuple(value.retained),tuple(tuple(pair) for pair in value.required))


@dataclass(frozen=True)
class EvidenceOrigin:
    identity: tuple[str,str,str]
    chunk: OwnedMap
    metadata: OwnedMap
    derived: tuple[OwnedMap,...]
    exact: bool
    sparse_rank: int | None
    dense_rank: int | None
    cosine: float
    rrf: float
    calibration: OwnedMap
    conflicts: tuple[ConflictDecision,...]

    def record(self):
        return dict(identity=list(self.identity),chunk=export(self.chunk),source_metadata=export(self.metadata),source_attribution=source_attribution(self.chunk),
            derived_texts=export(self.derived),exact=self.exact,sparse_rank=self.sparse_rank,dense_rank=self.dense_rank,
            cosine=self.cosine,rrf=self.rrf,calibration=export(self.calibration),conflicts=[asdict(item) for item in self.conflicts])


def capture_origin(item):
    row=own(item.chunk)
    return EvidenceOrigin(tuple(item.pack.identity),row,own(source_metadata(item.pack,row)),
        own(item.pack.derived_by_chunk.get(row['chunk_id'],())),item.exact,item.sparse_rank,item.dense_rank,
        item.dense_cosine,item.rrf,own(item.pack.manifest['calibration']),tuple(own_conflict(v) for v in item.conflicts))


@dataclass(frozen=True)
class EvidencePack:
    identity: tuple[str,str,str]
    manifest: OwnedMap
    relations: tuple[OwnedMap,...]
    derived_by_chunk: OwnedMap


@dataclass(frozen=True)
class FrozenEvidence:
    pack: EvidencePack
    chunk: OwnedMap
    exact: bool
    sparse_rank: int | None
    dense_rank: int | None
    dense_cosine: float
    rrf: float
    relevant: bool
    origins: tuple[tuple[str,str,str],...]
    origin_records: tuple[EvidenceOrigin,...]
    conflicts: tuple[ConflictDecision,...]
    final_rank: int | None
    rendering: GeneratorRepresentation

    @property
    def origin_key(self):
        return f"{self.pack.identity[0]}@{self.pack.identity[1]}:{self.pack.identity[2]}#{self.chunk['chunk_id']}"


def freeze_candidate(item):
    identity=tuple(item.pack.identity)
    row=own(item.chunk)
    pack=EvidencePack(identity,own(item.pack.manifest),own(item.pack.relations),own(item.pack.derived_by_chunk))
    rendering=select_representation(row,pack.derived_by_chunk.get(row['chunk_id'],()))
    origins=tuple(tuple(value) for value in item.origins)
    records=tuple(item.origin_records) if item.origin_records else (capture_origin(item),)
    if identity!=tuple(item.pack.identity):raise RuntimeContractError('ACTIVE_PACK_CHANGED')
    return FrozenEvidence(pack,row,item.exact,item.sparse_rank,item.dense_rank,item.dense_cosine,item.rrf,item.relevant,
        origins,records,tuple(own_conflict(v) for v in item.conflicts),item.final_rank,rendering)


@dataclass(frozen=True)
class GenerationContext:
    query: object
    identities: tuple[tuple[str,str,str],...]
    profile: OwnedMap
    generator: OwnedMap
    normalized_query: str


def freeze_context(query,identities,tokenizer,profile=None):
    # Local import avoids a retrieval/evidence import cycle. Query owns scalars.
    from .retrieval import Query
    values=tuple(sorted(tuple(value) for value in identities))
    if len({value[0] for value in values})!=len(values):raise RuntimeContractError('ACTIVE_PACK_CHANGED')
    return GenerationContext(Query(query.raw,query.as_of,query.jurisdiction,query.current_law),values,
        own(PROFILE if profile is None else profile),own(getattr(tokenizer,'metadata',{})),query.normalized)
