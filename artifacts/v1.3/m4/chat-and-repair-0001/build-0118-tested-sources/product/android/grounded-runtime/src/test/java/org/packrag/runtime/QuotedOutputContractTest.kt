package org.packrag.runtime

import org.junit.Assert.*
import org.junit.Test
import org.packrag.generator.QuoteProtocol

class QuotedOutputContractTest {
    @Test fun independentFinalGateRejectsInventedCitedTextAndLimitedOrMalformedGeneration() {
        val units=QuoteProtocol.units(listOf("Disconnect power before opening."))
        val correct="PRIVATE_ONLY_IN_MEMORY</think>1. Disconnect power before opening. [S1]"
        assertEquals("ANSWER_ACCEPTED",OutputValidator.validate(correct,setOf("S1"),quoteUnits=units).state)
        val rejected=OutputValidator.validate("PRIVATE_ONLY_IN_MEMORY</think>1. Open while powered. [S1]",setOf("S1"),quoteUnits=units)
        assertEquals("OUTPUT_REJECTED",rejected.state);assertNull(rejected.text);assertTrue(rejected.citations.isEmpty())
        assertEquals("GENERATION_UNUSABLE",OutputValidator.validate(correct,setOf("S1"),true,units).state)
        assertEquals("GENERATION_UNUSABLE",OutputValidator.validate(correct+"</think>",setOf("S1"),quoteUnits=units).state)
        assertEquals("INSUFFICIENT_EVIDENCE",OutputValidator.validate("private</think>INSUFFICIENT_EVIDENCE",setOf("S1"),quoteUnits=units).state)
        assertFalse(rejected.toString().contains("PRIVATE_ONLY_IN_MEMORY"))
    }
}
