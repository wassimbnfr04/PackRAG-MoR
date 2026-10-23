package org.packrag.product

import java.util.Locale
import org.junit.Assert.*
import org.junit.Test
import org.packrag.generator.GeneratorIdentity
import org.packrag.model.*
import org.packrag.runtime.*

class DiagnosticPresentationTest {
    @Test fun timingKeepsMeasuredZeroAndUsesExplicitUnitsIndependentOfLocale() {
        val prior=Locale.getDefault()
        try { Locale.setDefault(Locale.FRANCE)
            assertEquals("0.000 ms",measuredMilliseconds(0.0));assertEquals("1.250 ms",measuredMilliseconds(1.25))
            assertEquals("Not measured",measuredMilliseconds(null));assertEquals("0",measuredCount(0))
        } finally { Locale.setDefault(prior) }
    }
    @Test fun missingAndInvalidNumbersCannotBecomeZeroOrThroughput() {
        for(value in listOf(-1.0,Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY))
            assertEquals("Unavailable (invalid measurement)",measuredMilliseconds(value))
        assertEquals("Unknown",measuredCount(null));assertEquals("Unavailable (invalid count)",measuredCount(-1))
        val labels=diagnosticLines(RuntimeTrace(Answer("NO_ACTIVE_PACK"),emptyList(),totalMs=0.0)).map { it.label }
        assertFalse(labels.any { it.contains("tokens per second",true) || it.contains("visible",true) })
    }
    @Test fun coldWarmAndPreviouslyLoadedNoPackKeepSessionScopeAndUnknownPartitions() {
        val assets=ConfiguredAssets("model","artifact","configured quantization","{}")
        val identity=GeneratorIdentity("a".repeat(64),"b".repeat(64),"revision","backend")
        val cold=RuntimeTrace(Answer("ANSWER_ACCEPTED"),emptyList(),prefillTokens=100,evidenceTokens=30,emittedTokens=42,
            totalMs=20.0,initializationMs=7.0,session=SessionDiagnostics(assets,true,identity,5.0))
        val warm=cold.copy(initializationMs=0.0)
        assertEquals("7.000 ms",diagnosticLines(cold).single { it.label=="This query's lazy initialization" }.value)
        assertEquals("0.000 ms",diagnosticLines(warm).single { it.label=="This query's lazy initialization" }.value)
        assertEquals("5.000 ms",diagnosticLines(warm).single { it.label=="Generator constructor hash verification and load" }.value)
        val noPack=warm.copy(answer=Answer("NO_ACTIVE_PACK"),emittedTokens=0)
        val lines=diagnosticLines(noPack).associate { it.label to it.value }
        assertEquals("Not reached",lines["Generation in this query"]);assertEquals("true",lines["Model loaded in this session"])
        assertEquals("Unknown",lines["Reasoning emission (through closing marker)"])
        assertEquals("Unknown",lines["Remaining emission (final plus terminal)"])
        assertTrue(lines.keys.any { it.contains("excludes queue/session construction/UI") })
    }
    @Test fun returnedEmptyIsNotMissingAndHiddenFirstTokenIsLabelled() {
        val context=GenerationContext(Query("original question","2026-10-10"),emptyList(),FrozenProfile(),null,emptyList())
        val trace=RuntimeTrace(Answer("NO_RELEVANT_EVIDENCE"),emptyList(),totalMs=2.0,
            diagnostics=QueryDiagnostics(context,emptyList(),1.0,0.0,null,false))
        val lines=diagnosticLines(trace).associate { it.label to it.value }
        assertEquals("0",lines["Returned candidate pool"]);assertEquals("Not reached",lines["Generation in this query"])
        assertEquals("Not measured",lines["First emitted model token (may be hidden reasoning)"])
        assertEquals("Not returned",diagnosticLines(trace.copy(diagnostics=null)).single { it.label=="Returned candidate pool" }.value)
    }
    @Test fun actualSelectionMembershipAndLastRecordedDecisionRemainSeparate() {
        val trace=RuntimeTrace(Answer("INPUT_TOO_LONG"),emptyList(),totalMs=0.0,
            selection=SelectionPlan(listOf("a"),listOf(SelectionDecision("b","trial"),SelectionDecision("b","budget")),listOf("s")))
        assertEquals("Selected",candidateSelection(trace,"a"));assertEquals("budget",candidateSelection(trace,"b"))
        assertEquals("Not selected",candidateSelection(trace,"other"))
        assertEquals("Selection not reached",candidateSelection(trace.copy(selection=null),"a"))
    }
}
