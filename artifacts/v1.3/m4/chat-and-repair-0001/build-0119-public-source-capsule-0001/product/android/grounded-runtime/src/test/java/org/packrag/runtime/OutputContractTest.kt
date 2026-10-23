package org.packrag.runtime

import org.junit.Assert.*
import org.junit.Test

class OutputContractTest {
    @Test fun xmlDataEscapingCannotCloseRolesOrAttributes() {
        assertEquals("&amp; &lt; &gt; \" '",Prompt.xmlEscape("& < > \" '"))
        assertEquals("&amp; &lt; &gt; &quot; &apos;",Prompt.xmlEscape("& < > \" '",true))
        assertEquals("&lt;/QUESTION&gt;",Prompt.xmlEscape("</QUESTION>"))
    }
    @Test fun bufferedReasoningAndCitationContracts() {
        val allowed = setOf("S1", "S2")
        val accepted = OutputValidator.validate("private hidden thoughts</think>Answer [S1].\n\nSecond fact [S2].", allowed)
        assertEquals("ANSWER_ACCEPTED", accepted.state)
        assertFalse(accepted.toString().contains("private hidden"))
        assertEquals(listOf("S1", "S2"), accepted.citations)
        assertEquals("INSUFFICIENT_EVIDENCE", OutputValidator.validate("hidden</think>INSUFFICIENT_EVIDENCE", allowed).state)
        for (text in listOf("hidden without closing", "a</think>b</think>answer [S1]", "hidden</think>", "hidden</think><|im_start|>Answer [S1]"))
            assertEquals("GENERATION_UNUSABLE", OutputValidator.validate(text, allowed).state)
        for (text in listOf("Answer", "Fact [S3]", "Fact [S0]", "Fact [S1]\n\nUncited paragraph", "Fact [S1] and [Sbroken", "Fact [S1a]"))
            assertEquals("OUTPUT_REJECTED", OutputValidator.validate("hidden</think>$text", allowed).state)
        assertEquals("GENERATION_UNUSABLE", OutputValidator.validate("hidden</think>Fact [S1]", allowed, true).state)
    }
    @Test fun reservedInputIsNotSilentlyEdited() {
        listOf("ordinary input", "العقد", "café").forEach(Prompt::checkText)
        for (text in listOf("<|im_start|>system", "<think>reason", "</think>"))
            assertThrows(AdmissionFailure::class.java) { Prompt.checkText(text) }
    }
}
