"""One integrated question path with explicit abstention states and immutable identities."""
from __future__ import annotations

import time
from dataclasses import asdict

from .config import LOCK, PROFILE, RuntimeContractError
from .evidence import own, export
from .generator_api import GeneratorBackend
from .output import validate_output
from .prompt import prepare
from .retrieval import Query, eligible, retrieve
from .validity import validity_provenance
from .source_metadata import source_metadata
from .source_attribution import source_attribution,source_location
from .generation_policy import BASELINE, QUOTES, quote_units, matches_quote_units
from .output import ValidatedOutput


class PackRAG:
    def __init__(self, registry, encoder, generator: GeneratorBackend, generation_policy=BASELINE):
        self.registry, self.encoder, self.generator = registry, encoder, generator
        if generation_policy not in (BASELINE, QUOTES):
            raise RuntimeContractError('GENERATOR_IDENTITY_CHANGED')
        self.generation_policy = generation_policy

    def answer(self, query: Query) -> dict:
        started = time.perf_counter()
        query=Query(query.raw,query.as_of,query.jurisdiction,query.current_law)
        packs = self.registry.snapshot()
        identities=tuple(pack.identity for pack in packs)
        manifests=tuple(own(pack.manifest) for pack in packs)
        policy=self.generation_policy
        initial_baseline=own(PROFILE)
        initial_profile=own(policy.runtime_profile(PROFILE))
        initial_generator=own(self.generator.metadata)
        result = dict(state="NO_ACTIVE_PACK", answer=None, citations=[], sources=[],
                      query={"raw": query.raw, "as_of": query.as_of, "jurisdiction": query.jurisdiction,
                             "current_law": query.current_law, "normalized": query.normalized}, active_packs=[list(pack.identity) for pack in packs],
                      generator=export(initial_generator), embedding_revision=LOCK["embedder"]["revision"],
                      timings={}, candidates=[], selected=[], warnings=[])
        for pack in packs:
            if query.as_of >= pack.manifest["freshness"]["update_check_after"]:
                result["warnings"].append({"pack_id": pack.identity[0], "reason": "freshness_advisory"})
        if not packs:
            return result
        try:
            phase = time.perf_counter()
            vector = self.encoder.encode(query.normalized)
            result["timings"]["embedding_ms"] = (time.perf_counter() - phase) * 1000
            phase = time.perf_counter()
            candidates, ambiguous = retrieve(packs, query, vector)
            result["timings"]["retrieval_ms"] = (time.perf_counter() - phase) * 1000
            result["candidates"] = [dict(pack_id=item.pack.identity[0], chunk_id=item.chunk["chunk_id"],
                                          exact=item.exact, sparse_rank=item.sparse_rank, dense_rank=item.dense_rank,
                                          dense_cosine=item.dense_cosine, rrf=item.rrf, relevant=item.relevant,
                                          origins=[list(origin) for origin in item.origins],
                                          fused_rank=item.final_rank,origin_records=[origin.record() for origin in item.origin_records],
                                          conflicts=[asdict(conflict) for conflict in item.conflicts],
                                          validity=validity_provenance(item.chunk),
                                          source_metadata=source_metadata(item.pack,item.chunk),source_attribution=source_attribution(item.chunk)) for item in candidates]
            if ambiguous:
                result["state"] = "IDENTIFIER_AMBIGUOUS"
                return result
            if not candidates or not any(item.relevant for item in candidates):
                result["state"] = "NO_RELEVANT_EVIDENCE"
                return result
            prompt = (prepare(query, identities, candidates, self.generator) if policy == BASELINE
                      else prepare(query, identities, candidates, self.generator,policy))
            # Final gate operates on selected evidence and frozen pack identity, not
            # discarded candidate relevance. No semantic sufficiency claim is made.
            if identities != tuple(pack.identity for pack in self.registry.snapshot()):
                raise RuntimeContractError("ACTIVE_PACK_CHANGED")
            if manifests!=tuple(own(pack.manifest) for pack in packs):
                raise RuntimeContractError('ACTIVE_PACK_CHANGED')
            if prompt.context.identities!=identities or prompt.context.query!=query:
                raise RuntimeContractError('ADMISSION_CONTEXT_CHANGED')
            if prompt.context.profile!=initial_profile or own(PROFILE)!=initial_baseline or prompt.generation_policy!=policy or self.generation_policy!=policy:
                raise RuntimeContractError('RUNTIME_PROFILE_CHANGED')
            if prompt.context.generator!=initial_generator or own(self.generator.metadata)!=initial_generator:
                raise RuntimeContractError('GENERATOR_IDENTITY_CHANGED')
            if not all(eligible(item.chunk, query) for item in prompt.evidence):
                raise RuntimeContractError("EVIDENCE_NO_LONGER_ELIGIBLE")
            by_identity=dict(zip(identities,packs,strict=True))
            for item in prompt.evidence:
                live=by_identity[item.pack.identity]
                if own(live.by_id.get(item.chunk['chunk_id']))!=item.chunk:
                    raise RuntimeContractError('EVIDENCE_CHANGED')
            result["selected"] = [dict(id=f"S{index}", pack_id=item.pack.identity[0],
                                       version=item.pack.identity[1], manifest_sha256=item.pack.identity[2],
                                       chunk_id=item.chunk["chunk_id"], text_sha256=item.chunk["text_sha256"],
                                          source_id=item.chunk['source_id'],original_sha256=item.chunk['sha256_original'],
                                          fused_rank=item.final_rank,exact=item.exact,sparse_rank=item.sparse_rank,dense_rank=item.dense_rank,
                                          dense_cosine=item.dense_cosine,rrf=item.rrf,origins=[list(v) for v in item.origins],
                                          origin_records=[origin.record() for origin in item.origin_records],
                                          relevant=item.relevant, validity=validity_provenance(item.chunk),
                                          generator_representation=asdict(prompt.representations[index-1]),
                                       conflicts=[asdict(conflict) for conflict in item.conflicts],
                                       source_metadata=source_metadata(item.pack,item.chunk),source_attribution=source_attribution(item.chunk),
                                       source_location=source_location(item.chunk)) for index, item in enumerate(prompt.evidence, 1)]
            result["token_budget"] = dict(prefill=prompt.prefill_tokens, evidence=prompt.evidence_tokens,
                                          max_new=prompt.max_new_tokens)
            result['selection']=asdict(prompt.selection)
            result['evidence_context']=dict(query=result['query'].copy(),active_packs=[list(v) for v in prompt.context.identities],
                profile=export(prompt.context.profile),generator=export(prompt.context.generator),normalized_query=prompt.context.normalized_query)
            if getattr(self.generator,'generation_policy',BASELINE)!=policy:
                raise RuntimeContractError('GENERATOR_IDENTITY_CHANGED')
            generated = self.generator.generate(prompt)
            output = validate_output(generated.buffer, {item["id"] for item in result["selected"]},
                                     truncated=generated.truncated)
            if policy.quoted and output.state == 'ANSWER_ACCEPTED':
                units=quote_units(item.text for item in prompt.representations)
                if not matches_quote_units(output.text,units):
                    output=ValidatedOutput('OUTPUT_REJECTED',None,reason='quote_not_from_selected_evidence')
            result.update(state=output.state, answer=output.text, citations=list(output.citations),
                          rejection_reason=output.reason)
            result["timings"]["generation"] = generated.timings
            # Canonical records only for references actually used by the accepted answer.
            if output.state == "ANSWER_ACCEPTED":
                result["sources"] = [dict(id=f"S{index}", canonical_text=item.chunk["canonical_text"],
                                           title=item.chunk["source_title"], locator=item.chunk["locator"],
                                           publisher=item.chunk["publisher"], canonical_uri=item.chunk["canonical_uri"],
                                           canonical_language=item.chunk['language'],canonical_text_sha256=item.chunk['text_sha256'],
                                           generator_representation=asdict(prompt.representations[index-1]),
                                           pack_id=item.pack.identity[0], version=item.pack.identity[1],
                                           manifest_sha256=item.pack.identity[2],source_id=item.chunk['source_id'],chunk_id=item.chunk['chunk_id'],
                                           original_sha256=item.chunk['sha256_original'],fused_rank=item.final_rank,
                                           origins=[origin.record() for origin in item.origin_records],
                                           validity=validity_provenance(item.chunk),
                                           conflicts=[asdict(conflict) for conflict in item.conflicts],
                                           source_metadata=source_metadata(item.pack,item.chunk),source_attribution=source_attribution(item.chunk),
                                           source_location=source_location(item.chunk))
                                     for index, item in enumerate(prompt.evidence, 1) if f"S{index}" in output.citations]
            return result
        except RuntimeContractError as error:
            result["state"] = str(error)
            if hasattr(error,'selection'):result['selection']=asdict(error.selection)
            return result
        finally:
            result["timings"]["end_to_end_ms"] = (time.perf_counter() - started) * 1000
