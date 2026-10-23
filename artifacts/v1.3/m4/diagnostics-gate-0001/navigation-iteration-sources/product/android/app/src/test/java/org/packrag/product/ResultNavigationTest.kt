package org.packrag.product

import org.junit.Assert.*
import org.junit.Test
import org.packrag.model.Answer
import org.packrag.model.PackIdentity
import org.packrag.model.SourceRecord

class ResultNavigationTest {
    private val source=SourceRecord("S1","original canonical","title","locator","publisher",PackIdentity("p","1.0.0","a".repeat(64)))
    private val answer=Answer("ANSWER_ACCEPTED","original answer [S1]",listOf(source))
    @Test fun restoredIdentifiersReturnOnlyTheSameCompletedOwnedSource() {
        assertSame(source,capturedSource(answer,"result-a","S1","result-a"))
        assertNull(capturedSource(answer,"result-a","S2","result-a"))
    }
    @Test fun processLossMissingAnswerOrMissingIdentityCannotRestoreOldCitation() {
        assertNull(capturedSource(null,"result-a","S1","result-a"))
        assertNull(capturedSource(answer,null,"S1","result-a"))
        assertNull(capturedSource(answer,null,"S1",null))
        assertNull(capturedSource(answer,"result-a","S1",null))
        assertNull(capturedSource(answer,"result-a",null,"result-a"))
    }
    @Test fun repeatedS1InAReplacementAndAmbiguousRecordsCannotRebindOldNavigation() {
        val replacement=Answer("ANSWER_ACCEPTED","replacement [S1]",listOf(source.copy(canonicalText="new canonical")))
        assertNull(capturedSource(replacement,"result-b","S1","result-a"))
        assertEquals("new canonical",capturedSource(replacement,"result-b","S1","result-b")?.canonicalText)
        assertNull(capturedSource(answer.copy(sources=listOf(source,source)),"result-a","S1","result-a"))
    }
}
