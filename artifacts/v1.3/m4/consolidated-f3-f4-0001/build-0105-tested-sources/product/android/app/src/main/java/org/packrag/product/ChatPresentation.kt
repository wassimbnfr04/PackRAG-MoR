package org.packrag.product

import org.packrag.model.Answer
import org.packrag.model.SourceRecord
import org.packrag.model.ownedList

/** Session-only final outputs. No raw reasoning, runtime/session handles or disk history. */
class ChatTurn(val resultId:String,submission:SubmittedQuery,answer:Answer) {
    val submission=SubmittedQuery(submission.query,submission.packs)
    val answer=answer.copy(sources=ownedList(answer.sources.map { source ->
        source.copy(conflicts=ownedList(source.conflicts),originRecords=ownedList(source.originRecords),
            metadata=source.metadata?.let{it.copy(relations=ownedList(it.relations))})
    }))
    init { require(resultId.isNotBlank()) }
}

fun appendChatTurn(previous:List<ChatTurn>,turn:ChatTurn):List<ChatTurn> =
    ownedList((previous.filterNot{it.resultId==turn.resultId}+turn).takeLast(12))

/** S1 is local to a result, never a cross-turn lookup key. */
fun chatSource(turns:List<ChatTurn>,resultId:String?,evidenceId:String?):SourceRecord? {
    if(resultId==null || evidenceId==null)return null
    return turns.singleOrNull{it.resultId==resultId}?.answer?.sources?.singleOrNull{it.evidenceId==evidenceId}
}
