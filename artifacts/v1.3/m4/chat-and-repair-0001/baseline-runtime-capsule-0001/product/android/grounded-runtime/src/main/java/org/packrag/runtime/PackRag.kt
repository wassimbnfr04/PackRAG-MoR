package org.packrag.runtime

import org.packrag.embedding.GraniteEncoder
import org.packrag.generator.GeneratorBackend
import org.packrag.model.Answer
import org.packrag.model.PackIdentity
import org.packrag.model.Query
import org.packrag.model.SourceRecord
import org.packrag.model.eligible
import org.packrag.model.validityProvenance
import org.packrag.model.sourceMetadata
import org.packrag.model.SelectionPlan
import org.packrag.model.FrozenEvidence
import org.packrag.packs.PackRegistry
import org.packrag.retrieval.Retrieval
import java.util.concurrent.atomic.AtomicLong

/** Trace exposes numeric metadata and final output only, never a raw reasoning buffer. */
data class RuntimeTrace(val answer: Answer, val selected: List<String>, val prefillTokens: Int = 0,
    val evidenceTokens: Int = 0, val emittedTokens: Int = 0, val reasoningTokens: Int? = null,
    val finalAndTerminalTokens: Int? = null, val prefillMs: Double? = null, val decodeWallMs: Double? = null,
    val firstEmittedTokenMs: Double? = null, val totalMs: Double, val initializationMs: Double = 0.0,
    val selection:SelectionPlan?=null,val evidenceContext:GenerationContext?=null,val evidence:List<FrozenEvidence> = emptyList(),
    val diagnostics:QueryDiagnostics?=null,val session:SessionDiagnostics?=null)

class PackRag(private val registry: PackRegistry, private val encoder: GraniteEncoder, private val generator: GeneratorBackend,
    private val sparseLookup:(org.packrag.packs.ActivePack,String)->List<String> = { pack,terms -> pack.sparse(terms) }) {
    private val cancellation = AtomicLong(0)
    @Synchronized fun ask(query: Query, cancelled: () -> Boolean = { false }): RuntimeTrace = registry.withSnapshot { packs -> askFrozen(query,packs,cancelled) }
    private fun askFrozen(query: Query, packs: List<org.packrag.packs.ActivePack>, cancelled: () -> Boolean): RuntimeTrace {
        val start = System.nanoTime()
        val ticket = cancellation.get()
        fun elapsed() = (System.nanoTime() - start) / 1e6
        if (packs.isEmpty()) return RuntimeTrace(Answer("NO_ACTIVE_PACK"), emptyList(), totalMs = elapsed())
        var context:GenerationContext?=null
        var candidates:List<CandidateDiagnostic>?=null
        var embeddingMs:Double?=null;var retrievalMs:Double?=null;var admissionMs:Double?=null
        var generationCalled=false
        fun diagnostic()=context?.let { QueryDiagnostics(it,candidates,embeddingMs,retrievalMs,admissionMs,generationCalled) }
        try {
            val identities=packs.map { PackIdentity(it.id,it.version,it.manifestHash) }
            val manifests=packs.map { it.manifest.toString() }
            val generatorIdentity=generator.identity
            context=GenerationContext(query,identities,FrozenProfile(),generatorIdentity,manifests)
            val embeddingStart=System.nanoTime();val vector=encoder.encode(query.normalized)
            embeddingMs=(System.nanoTime()-embeddingStart)/1e6
            val retrievalStart=System.nanoTime();val retrieved = Retrieval.retrieve(packs, query, vector,sparseLookup)
            retrievalMs=(System.nanoTime()-retrievalStart)/1e6
            candidates=retrieved.candidates.map(::candidateDiagnostic)
            if (ticket != cancellation.get() || cancelled()) return RuntimeTrace(Answer("CANCELLED"), emptyList(), totalMs = elapsed(),diagnostics=diagnostic())
            if (retrieved.ambiguous) return RuntimeTrace(Answer("IDENTIFIER_AMBIGUOUS"), emptyList(), totalMs = elapsed(),diagnostics=diagnostic())
            if (retrieved.candidates.none { it.relevant }) return RuntimeTrace(Answer("NO_RELEVANT_EVIDENCE"), emptyList(), totalMs = elapsed(),diagnostics=diagnostic())
            val admissionStart=System.nanoTime()
            val prepared = try { Prompt.prepare(query, packs, retrieved.candidates, generator) }
                finally { admissionMs=(System.nanoTime()-admissionStart)/1e6 }
            if(prepared.evidence.any { !eligible(it.chunk,prepared.context.query) }) throw AdmissionFailure("EVIDENCE_NO_LONGER_ELIGIBLE")
            if(prepared.evidence.none { it.relevant }) throw AdmissionFailure("NO_RELEVANT_EVIDENCE")
            if(identities!=registry.snapshot().map { PackIdentity(it.id,it.version,it.manifestHash) }
                || identities!=prepared.context.identities || manifests!=prepared.context.manifests
                || manifests!=packs.map { it.manifest.toString() }) throw AdmissionFailure("ACTIVE_PACK_CHANGED")
            if(generatorIdentity!=prepared.context.generator || generatorIdentity!=generator.identity) throw AdmissionFailure("GENERATOR_IDENTITY_CHANGED")
            generationCalled=true
            val emission = generator.generate(prepared.tokens, prepared.maximum) { ticket != cancellation.get() || cancelled() }
            try {
                val closing = generator.tokenize("</think>").single()
                val partition = emission.emitted.indexOf(closing).takeIf { it >= 0 }?.plus(1)
                val output = if (emission.stop == 2) ValidatedOutput("CANCELLED") else OutputValidator.validate(
                    emission.buffer.toString(Charsets.UTF_8), prepared.evidence.indices.map { "S${it + 1}" }.toSet(), emission.stop == 1)
                val sources = output.citations.map { id ->
                    val candidate = prepared.evidence[id.drop(1).toInt() - 1]
                    SourceRecord(id, candidate.chunk.canonicalText, candidate.chunk.sourceTitle, candidate.chunk.locator,
                        candidate.chunk.publisher, candidate.packIdentity,
                        validityProvenance(candidate.chunk), candidate.metadata,candidate.conflicts,
                        candidate.chunk.language,candidate.chunk.textSha256,prepared.representations[id.drop(1).toInt()-1],
                        candidate.chunk.originalSha256,candidate.chunk.id,candidate.chunk.sourceId,candidate.finalRank,candidate.originRecords,
                        candidate.chunk.attribution,candidate.chunk.location)
                }
                return RuntimeTrace(Answer(output.state, output.text, sources), prepared.evidence.map { it.chunk.id },
                    prepared.tokens.size, prepared.evidenceTokens, emission.emitted.size, partition,
                    partition?.let { emission.emitted.size - it }, emission.prefillMs, emission.decodeWallMs,
                    emission.firstEmittedTokenMs.takeIf { it >= 0 }, elapsed(),selection=prepared.selection,evidenceContext=prepared.context,evidence=prepared.evidence,diagnostics=diagnostic())
            } finally { emission.buffer.fill(0) }
        } catch (failure: AdmissionFailure) {
            return RuntimeTrace(Answer(failure.state), emptyList(), totalMs = elapsed(),selection=failure.selection,diagnostics=diagnostic())
        }
    }
    fun cancel() { cancellation.incrementAndGet(); generator.cancel() }
}
