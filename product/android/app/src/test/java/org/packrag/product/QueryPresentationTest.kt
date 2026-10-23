package org.packrag.product

import org.junit.Assert.*
import org.junit.Test
import org.packrag.model.PackIdentity

class QueryPresentationTest {
    @Test fun strictFormInputsUseTheSharedRuntimeContract() {
        val raw = "  Ａｓｔｅｒ－９ temperature?  "
        val q = submittedQuery(raw,"2028-02-29","MA-01",true)
        assertEquals(raw,q.raw);assertEquals("aster-9 temperature?",q.normalized)
        assertEquals("2028-02-29",q.asOf);assertEquals("MA-01",q.jurisdiction);assertTrue(q.currentLaw)
        assertNull(submittedQuery("question","2026-10-10","",false).jurisdiction)
        assertEquals("MA",submittedQuery("question","2026-10-10","MA",false).jurisdiction)
        for(date in listOf("2027-02-29","2026-04-31","0000-01-01","2026-1-01"," 2026-10-10","2026-10-10 "))
            assertEquals("INVALID_QUERY_DATE",failure("question",date,""))
        for(code in listOf("ma"," MA","MA ","M","MA-1234","MA_01"," "))
            assertEquals("INVALID_QUERY_JURISDICTION",failure("question","2026-10-10",code))
        for(text in listOf(""," \t\n","\u0085","\u2007")) assertEquals("EMPTY_QUESTION",failure(text,"2026-10-10",""))
        for(text in listOf("\uD800","\uDC00")) assertEquals("INVALID_QUERY_TEXT",failure(text,"2026-10-10",""))
    }
    private fun failure(text:String,date:String,code:String):String? =
        try { submittedQuery(text,date,code,false);fail("Invalid control was accepted");null }
        catch(expected:IllegalArgumentException) { expected.message }

    @Test fun freshnessIsInclusiveAdvisoryAndCapturedValuesAreOwned() {
        val first = PackFreshness(PackIdentity("org.test.first","1.0.0","a".repeat(64)),"2027-01-01")
        val second = PackFreshness(PackIdentity("org.test.second","2.0.0","b".repeat(64)),"2027-02-01")
        assertFalse(first.advisoryAt("2026-12-31"));assertTrue(first.advisoryAt("2027-01-01"));assertTrue(first.advisoryAt("2027-01-02"))
        val list = mutableListOf(first,second)
        val captured = SubmittedQuery(submittedQuery("original","2027-01-01","MA",true),list)
        list.clear()
        submittedQuery("edited","2026-10-10","",false)
        assertEquals(2,captured.packs.size);assertEquals(listOf(first),captured.packs.filter { it.advisoryAt(captured.query.asOf) })
        assertEquals("original",captured.query.raw);assertEquals("2027-01-01",captured.query.asOf);assertEquals("MA",captured.query.jurisdiction);assertTrue(captured.query.currentLaw)
        try { (captured.packs as MutableList).clear();fail("Owned context mutated") } catch(expected:UnsupportedOperationException) { }
    }

    @Test fun deterministicOutcomesHaveDistinctActionableGuidance() {
        assertTrue(answerGuidance("NO_ACTIVE_PACK").contains("activate"))
        assertTrue(answerGuidance("NO_RELEVANT_EVIDENCE").contains("date/jurisdiction"))
        assertTrue(answerGuidance("INSUFFICIENT_EVIDENCE").contains("insufficient"))
        assertTrue(answerGuidance("OUTPUT_REJECTED").contains("No candidate answer"))
        assertTrue(answerGuidance("CANCELLED").contains("cancelled"))
        assertTrue(answerGuidance("RUNTIME_ERROR").contains("local assets"))
        assertTrue(answerGuidance("EVIDENCE_BUDGET_EXCEEDED").contains("EVIDENCE_BUDGET_EXCEEDED"))
        assertTrue(queryInputGuidance("INVALID_QUERY_DATE").contains("YYYY-MM-DD"))
        assertTrue(queryInputGuidance("INVALID_QUERY_JURISDICTION").contains("MA-01"))
    }
}
