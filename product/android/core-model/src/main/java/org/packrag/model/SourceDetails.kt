package org.packrag.model

/** Authenticated metadata assertions, not external licensing/review/semantic approval. */
data class SourceAttribution(val canonicalUri:String?,val retrievedAt:String?,val license:String?,
    val redistributionAllowed:Boolean?,val sourceType:String?,val snapshotPath:String?,val notes:String?=null)

data class SourceLocation(val chunkTitle:String?,val section:String?,val pageStart:Long?,val pageEnd:Long?,
    val characterStart:Long?,val characterEnd:Long?)

data class PackSourceDetails(val sourceId:String,val title:String,val publisher:String,val language:String,
    val originalSha256:String,val attribution:SourceAttribution,val sourceFrom:String?,val sourceUntilExcl:String?,
    val jurisdiction:String?,val legalStatus:String?,val authorityRank:Int?,val documentVersion:String?,val issuedAt:String?)

/** Owned public values read from a fresh verified private snapshot; no reader/path/JSON object escapes. */
class PackDetails(val identity:PackIdentity,val name:String,val domain:String,val publisherName:String,
    val publisherKeyId:String,val releaseTimestamp:String,val updateCheckAfter:String,
    languages:List<String>,jurisdictions:List<String>,val embeddingProfileJson:String,val buildJson:String,
    val calibrationJson:String,val calibrationStatus:String,val manifestBytes:Long,val payloadBytes:Long,
    val transportBytes:Long,val chunkCount:Int,sources:List<PackSourceDetails>) {
    val languages=ownedList(languages)
    val jurisdictions=ownedList(jurisdictions)
    val sources=ownedList(sources)
}
