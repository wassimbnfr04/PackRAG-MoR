package org.packrag.model

/** Copied values from a complete freshly verified installed snapshot, not external approval. */
data class PackOverview(val identity:PackIdentity,val name:String,val publisherName:String,
    val publisherKeyId:String,val updateCheckAfter:String,val manifestBytes:Long,
    val payloadBytes:Long,val transportBytes:Long) {
    init {
        TemporalDates.date(updateCheckAfter)
        require(manifestBytes>=0 && payloadBytes>=0 && transportBytes>=0)
    }
}
