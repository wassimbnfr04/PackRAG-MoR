package org.packrag.sources

import org.packrag.model.*

data class DetailLine(val label:String,val value:String)
fun unknown(value:Any?):String=value?.toString() ?: "Unknown"
fun attributionLines(value:SourceAttribution?):List<DetailLine> = listOf(
    DetailLine("Canonical URI",unknown(value?.canonicalUri)),DetailLine("Retrieved at",unknown(value?.retrievedAt)),
    DetailLine("Declared license",unknown(value?.license)),DetailLine("Declared redistribution allowed",unknown(value?.redistributionAllowed)),
    DetailLine("Source type",unknown(value?.sourceType)),DetailLine("Packaged snapshot path",value?.snapshotPath ?: "No packaged original snapshot"),
    DetailLine("Source notes",unknown(value?.notes)))
fun validityLines(value:ValidityProvenance?):List<DetailLine> = if(value==null) listOf(DetailLine("Validity","Unknown")) else listOf(
    DetailLine("Source start",unknown(value.sourceFrom)),DetailLine("Source end (exclusive)",unknown(value.sourceUntilExcl)),
    DetailLine("Chunk start",if(value.chunkStartInherits) "Inherits source start (${unknown(value.sourceFrom)})" else unknown(value.chunkFrom)),
    DetailLine("Chunk end (exclusive)",if(value.chunkEndInherits) "Inherits source end (${unknown(value.sourceUntilExcl)})" else unknown(value.chunkUntilExcl)),
    DetailLine("Effective intersection start",unknown(value.effectiveFrom)),DetailLine("Effective intersection end (exclusive)",unknown(value.effectiveUntilExcl)),
    DetailLine("Empty intersection",value.emptyIntersection.toString()),DetailLine("Jurisdiction",unknown(value.jurisdiction)),DetailLine("Legal status",unknown(value.legalStatus)))
fun sourceLines(value:SourceRecord):List<DetailLine> = listOf(
    DetailLine("Locator",value.locator),DetailLine("Publisher assertion",value.publisher),
    DetailLine("Pack identity","${value.pack.packId}@${value.pack.version}"),DetailLine("Manifest SHA-256",value.pack.manifestSha256),
    DetailLine("Source ID",unknown(value.sourceId)),DetailLine("Chunk ID",unknown(value.chunkId)),
    DetailLine("Canonical language",unknown(value.canonicalLanguage)),DetailLine("Canonical text SHA-256",unknown(value.canonicalTextSha256)),
    DetailLine("Original source SHA-256",unknown(value.originalSha256)),DetailLine("Fused rank",unknown(value.fusedRank)),
    DetailLine("Chunk title",unknown(value.location?.chunkTitle)),DetailLine("Section",unknown(value.location?.section)),
    DetailLine("Page start",unknown(value.location?.pageStart)),DetailLine("Page end",unknown(value.location?.pageEnd)),
    DetailLine("Character start",unknown(value.location?.characterStart)),DetailLine("Character end",unknown(value.location?.characterEnd)))+
    attributionLines(value.attribution)+validityLines(value.validity)+metadataLines(value.metadata)
fun metadataLines(value:SourceMetadata?):List<DetailLine> = listOf(
    DetailLine("Signing key",unknown(value?.publisherKeyId)),DetailLine("Authority rank assertion",unknown(value?.authorityRank)),
    DetailLine("Document version",unknown(value?.documentVersion)),DetailLine("Issued at",unknown(value?.issuedAt)),DetailLine("Article",unknown(value?.article)))+
    (value?.relations ?: emptyList()).map { DetailLine("Directed relation","${it.fromChunkId} → ${it.toChunkId}: ${it.relationType}; provenance ${it.provenance}; confidence ${it.confidence}") }
fun conflictLines(values:List<ConflictDecision>):List<DetailLine> = values.map {
    DetailLine("Conflict decision","${it.state}: ${it.reason}; members ${it.members.joinToString()}; preferred ${unknown(it.preferred)}; retained ${it.retained.joinToString()}; required ${it.required.joinToString()}") }
