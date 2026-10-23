package org.packrag.product

import org.packrag.model.Answer
import org.packrag.model.SourceRecord

/** Saved navigation stores identifiers only; the completed ViewModel owns data. */
fun capturedSource(answer:Answer?,completedResultId:String?,evidenceId:String?,sourceResultId:String?):SourceRecord? {
    if(completedResultId==null || sourceResultId==null || evidenceId==null || completedResultId!=sourceResultId) return null
    return answer?.sources?.singleOrNull { it.evidenceId==evidenceId }
}
