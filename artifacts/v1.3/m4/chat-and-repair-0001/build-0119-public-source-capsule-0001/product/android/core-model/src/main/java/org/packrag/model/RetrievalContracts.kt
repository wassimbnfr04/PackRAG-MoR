package org.packrag.model

data class Query(val raw: String, val asOf: String, val jurisdiction: String? = null, val currentLaw: Boolean = false) {
    val normalized:String
    init {
        var index=0
        while(index<raw.length) {
            val char=raw[index]
            if(Character.isHighSurrogate(char)) {
                require(index+1<raw.length && Character.isLowSurrogate(raw[index+1])) { "INVALID_QUERY_TEXT" }; index+=2
            } else { require(!Character.isLowSurrogate(char)) { "INVALID_QUERY_TEXT" }; index++ }
        }
        require(runCatching { TemporalDates.date(asOf) }.isSuccess) { "INVALID_QUERY_DATE" }
        require(jurisdiction==null || Regex("[A-Z]{2}(?:-[A-Z0-9]{1,3})?").matches(jurisdiction)) { "INVALID_QUERY_JURISDICTION" }
        normalized=normalizeQuery(raw)
        require(normalized.isNotEmpty()) { "EMPTY_QUESTION" }
    }
}

fun normalizeQuery(text: String): String = QueryUnicode.normalize(text)

data class Chunk(
    val id: String, val sourceId: String, val title: String, val sourceTitle: String, val section: String?,
    val locator: String, val canonicalText: String, val textSha256: String, val originalSha256: String,
    val denseRow: Int, val jurisdiction: String?, val sourceFrom: String?, val sourceUntil: String?,
    val effectiveFrom: String?, val effectiveUntil: String?, val legalStatus: String?,
    val publisher: String, val canonicalUri: String?, val language: String,
    val authorityRank: Int? = null, val documentVersion: String? = null, val issuedAt: String? = null, val article: String? = null,
    val attribution:SourceAttribution?=null,val location:SourceLocation?=null,
)

fun eligible(chunk: Chunk, query: Query): Boolean {
    if (query.jurisdiction != null && chunk.jurisdiction != query.jurisdiction) return false
    val validity = validityProvenance(chunk)
    val start = validity.effectiveFrom
    val end = validity.effectiveUntilExcl
    if (validity.emptyIntersection) return false
    if ((start != null && query.asOf < start) || (end != null && query.asOf >= end)) return false
    return !(query.currentLaw && chunk.legalStatus in setOf("repealed", "superseded"))
}

data class ValidityProvenance(
    val sourceFrom: String?, val sourceUntilExcl: String?, val chunkFrom: String?, val chunkUntilExcl: String?,
    val effectiveFrom: String?, val effectiveUntilExcl: String?,
    val sourceStartUnknown: Boolean, val sourceEndUnknown: Boolean,
    val chunkStartInherits: Boolean, val chunkEndInherits: Boolean, val emptyIntersection: Boolean,
    val jurisdiction: String?, val legalStatus: String?,
)

fun validityProvenance(chunk: Chunk): ValidityProvenance {
    val start = listOfNotNull(chunk.sourceFrom, chunk.effectiveFrom).maxOrNull()
    val end = listOfNotNull(chunk.sourceUntil, chunk.effectiveUntil).minOrNull()
    return ValidityProvenance(chunk.sourceFrom,chunk.sourceUntil,chunk.effectiveFrom,chunk.effectiveUntil,
        start,end,chunk.sourceFrom==null,chunk.sourceUntil==null,chunk.effectiveFrom==null,chunk.effectiveUntil==null,
        start!=null && end!=null && start>=end,chunk.jurisdiction,chunk.legalStatus)
}
