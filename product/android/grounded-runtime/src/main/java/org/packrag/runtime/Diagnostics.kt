package org.packrag.runtime

import org.packrag.generator.GeneratorIdentity
import org.packrag.model.EvidenceOrigin
import org.packrag.model.PackIdentity
import org.packrag.model.ownedList
import org.packrag.model.ownedOrigin
import org.packrag.retrieval.Candidate

/** Returned-pool observations only; no live reader or representation selection. */
class CandidateDiagnostic(val key:String,val identity:PackIdentity,val chunkId:String,val sourceId:String,
    val canonicalSha256:String,val originalSha256:String,val exact:Boolean,val sparseRank:Int?,val denseRank:Int?,
    val cosine:Double,val rrf:Double,val relevant:Boolean,val finalRank:Int?,origins:List<EvidenceOrigin>) {
    val origins=ownedList(origins.map(::ownedOrigin))
}

fun candidateDiagnostic(value:Candidate)=CandidateDiagnostic(value.originKey,value.packIdentity,value.chunk.id,value.chunk.sourceId,
    value.chunk.textSha256,value.chunk.originalSha256,value.exact,value.sparseRank,value.denseRank,value.cosine,value.rrf,
    value.relevant,value.finalRank,value.originRecords)

/** Null pool means retrieval did not return; an empty returned pool remains empty. */
class QueryDiagnostics(val context:GenerationContext,candidates:List<CandidateDiagnostic>?,val embeddingMs:Double?,
    val retrievalMs:Double?,val admissionMs:Double?,val generationCalled:Boolean) {
    val candidates=candidates?.let(::ownedList)
}

data class ConfiguredAssets(val modelId:String,val artifact:String,val quantization:String,val embedderProfileJson:String)
data class SessionDiagnostics(val configured:ConfiguredAssets,val embedderInitialized:Boolean,
    val generator:GeneratorIdentity?,val generatorLoadAndVerificationMs:Double?)
