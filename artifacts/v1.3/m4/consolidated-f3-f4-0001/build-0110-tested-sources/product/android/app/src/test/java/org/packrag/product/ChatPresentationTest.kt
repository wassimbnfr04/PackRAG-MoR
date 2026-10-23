package org.packrag.product

import org.junit.Assert.*
import org.junit.Test
import org.packrag.model.*

class ChatPresentationTest {
    private fun turn(id:String,text:String)=ChatTurn(id,SubmittedQuery(Query("Repair device $id","2026-10-12"),emptyList()),
        Answer("ANSWER_ACCEPTED",text,listOf(SourceRecord("S1",text,"Manual $id","Procedure","Test",PackIdentity(id,"1.0.0",id)))))
    @Test fun sameCitationIdCannotAliasAnotherCompletedQuestionOrMissingProcessResult() {
        val first=turn("first","Disconnect the power.");val second=turn("second","Remove the tube.")
        val rows=appendChatTurn(appendChatTurn(emptyList(),first),second)
        assertEquals("Disconnect the power.",chatSource(rows,"first","S1")!!.canonicalText)
        assertEquals("Remove the tube.",chatSource(rows,"second","S1")!!.canonicalText)
        assertNull(chatSource(rows,"missing","S1"));assertNull(chatSource(emptyList(),"first","S1"))
        assertNull(chatSource(rows,"first","S2"));assertNull(chatSource(rows,null,"S1"))
    }
    @Test fun repeatedCompletionIsDeduplicatedAndOldestEvictedWithoutRebindingItsSources() {
        var rows:List<ChatTurn> = emptyList()
        repeat(15){rows=appendChatTurn(rows,turn("turn$it","Step $it"))}
        assertEquals(12,rows.size);assertNull(chatSource(rows,"turn2","S1"))
        rows=appendChatTurn(rows,turn("turn14","Updated final output"))
        assertEquals(12,rows.size);assertEquals(1,rows.count{it.resultId=="turn14"})
        assertEquals("Updated final output",chatSource(rows,"turn14","S1")!!.canonicalText)
    }
    @Test fun callerMutableSourceListsCannotChangeCapturedHistory() {
        val sources=mutableListOf(SourceRecord("S1","Owned evidence","Title","Step","Test",PackIdentity("a","1","h")))
        val captured=ChatTurn("one",SubmittedQuery(Query("Repair device","2026-10-12"),emptyList()),Answer("ANSWER_ACCEPTED","A step [S1]",sources))
        sources.clear()
        assertEquals("Owned evidence",chatSource(listOf(captured),"one","S1")!!.canonicalText)
        assertThrows(UnsupportedOperationException::class.java){(captured.answer.sources as MutableList).clear()}
    }
}
