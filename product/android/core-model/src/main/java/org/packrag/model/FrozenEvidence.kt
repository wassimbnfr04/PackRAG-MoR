package org.packrag.model

import java.util.Collections

/** A val/List interface alone does not confer ownership. All nested lists copy. */
fun <T> ownedList(values:Collection<T>):List<T> = Collections.unmodifiableList(ArrayList(values))
fun ownedConflict(value:ConflictDecision)=value.copy(members=ownedList(value.members),
    retained=ownedList(value.retained),required=ownedList(value.required))
fun ownedMetadata(value:SourceMetadata)=value.copy(relations=ownedList(value.relations))

interface EvidenceView {
    val chunk:Chunk
    val packIdentity:PackIdentity
    val originKey:String
    val generatorRendering:GeneratorRepresentation
}

data class CalibrationSnapshot(val status:String,val agreed:Double?,val denseOnly:Double?)
data class EvidenceOrigin(val identity:PackIdentity,val chunk:Chunk,val metadata:SourceMetadata,
    val derived:List<DerivedText>,val exact:Boolean,val sparseRank:Int?,val denseRank:Int?,
    val cosine:Double,val rrf:Double,val calibration:CalibrationSnapshot,val conflicts:List<ConflictDecision>)

fun ownedOrigin(value:EvidenceOrigin)=value.copy(metadata=ownedMetadata(value.metadata),
    derived=ownedList(value.derived),conflicts=ownedList(value.conflicts.map(::ownedConflict)))

/** Owns costs, generation, diagnostics and citation values; no pack reader. */
class FrozenEvidence(override val packIdentity:PackIdentity,override val chunk:Chunk,
    val exact:Boolean,val sparseRank:Int?,val denseRank:Int?,val cosine:Double,val rrf:Double,val relevant:Boolean,
    origins:List<String>,originRecords:List<EvidenceOrigin>,conflicts:List<ConflictDecision>,val finalRank:Int?,
    metadata:SourceMetadata,override val generatorRendering:GeneratorRepresentation):EvidenceView {
    val origins=ownedList(origins)
    val originRecords=ownedList(originRecords.map(::ownedOrigin))
    val conflicts=ownedList(conflicts.map(::ownedConflict))
    val metadata=ownedMetadata(metadata)
    override val originKey:String="${packIdentity.packId}@${packIdentity.version}:${packIdentity.manifestSha256}#${chunk.id}"
}
