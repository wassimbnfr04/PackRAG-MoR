package org.packrag.model

object ProductProfile {
    const val CONTEXT = 2048
    const val PREFILL = 1536
    const val GENERATED = 512
    const val EVIDENCE = 1200
    const val EVIDENCE_CHUNKS = 4
    const val SPARSE_K = 24
    const val DENSE_K = 24
    const val RRF_K = 60
    const val LOCAL_FUSED_CAP = 16
    const val CROSS_PACK_CAP = 32
    const val EMBEDDING_DIM = 384
}

data class PackIdentity(val packId: String, val version: String, val manifestSha256: String)
data class SourceRecord(val evidenceId: String, val canonicalText: String, val title: String,
                        val locator: String, val publisher: String, val pack: PackIdentity,
                        val validity: ValidityProvenance? = null, val metadata: SourceMetadata? = null,
                        val conflicts:List<ConflictDecision> = emptyList(),val canonicalLanguage:String?=null,
                        val canonicalTextSha256:String?=null,val generatorRepresentation:GeneratorRepresentation?=null,
                        val originalSha256:String?=null,val chunkId:String?=null,val sourceId:String?=null,val fusedRank:Int?=null,
                        val originRecords:List<EvidenceOrigin> = emptyList(),
                        val attribution:SourceAttribution?=null,val location:SourceLocation?=null)

data class SourceRelation(val fromChunkId:String,val toChunkId:String,val relationType:String,val provenance:String,val confidence:Double)

data class SourceMetadata(val authorityRank:Int?,val documentVersion:String?,val issuedAt:String?,val article:String?,
                          val publisherKeyId:String,val relations:List<SourceRelation>)

/** Exposes signed fields verbatim; this function makes no ranking or source-truth decision. */
fun sourceMetadata(chunk:Chunk,publisherKeyId:String,relations:List<SourceRelation>)=SourceMetadata(
    chunk.authorityRank,chunk.documentVersion,chunk.issuedAt,chunk.article,publisherKeyId,
    relations.filter { it.fromChunkId==chunk.id || it.toChunkId==chunk.id })
data class Answer(val state: String, val text: String? = null, val sources: List<SourceRecord> = emptyList())
