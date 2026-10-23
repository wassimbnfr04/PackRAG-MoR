package org.packrag.product

import java.util.Locale
import org.packrag.runtime.RuntimeTrace

data class DiagnosticLine(val label:String,val value:String)
fun measuredMilliseconds(value:Double?):String=when {
    value==null -> "Not measured"
    !value.isFinite() || value<0 -> "Unavailable (invalid measurement)"
    else -> String.format(Locale.ROOT,"%.3f ms",value)
}
fun measuredCount(value:Int?):String=when {
    value==null -> "Unknown"
    value<0 -> "Unavailable (invalid count)"
    else -> value.toString()
}
fun diagnosticLines(trace:RuntimeTrace):List<DiagnosticLine> {
    val data=trace.diagnostics;val session=trace.session
    val generated=when { data!=null -> if(data.generationCalled) "Called" else "Not reached"
        trace.answer.state=="NO_ACTIVE_PACK" -> "Not reached";else -> "Unknown" }
    return listOf(
        DiagnosticLine("Completed outcome",trace.answer.state),DiagnosticLine("Generation in this query",generated),
        DiagnosticLine("Prefill tokens",measuredCount(trace.prefillTokens)),DiagnosticLine("Evidence tokens",measuredCount(trace.evidenceTokens)),
        DiagnosticLine("Emitted tokens (includes terminal)",measuredCount(trace.emittedTokens)),
        DiagnosticLine("Reasoning emission (through closing marker)",measuredCount(trace.reasoningTokens)),
        DiagnosticLine("Remaining emission (final plus terminal)",measuredCount(trace.finalAndTerminalTokens)),
        DiagnosticLine("First emitted model token (may be hidden reasoning)",measuredMilliseconds(trace.firstEmittedTokenMs)),
        DiagnosticLine("Backend prefill",measuredMilliseconds(trace.prefillMs)),DiagnosticLine("Backend decode wall",measuredMilliseconds(trace.decodeWallMs)),
        DiagnosticLine("Query embedding",measuredMilliseconds(data?.embeddingMs)),DiagnosticLine("Retrieval (includes sparse/dense/fusion/gates)",measuredMilliseconds(data?.retrievalMs)),
        DiagnosticLine("Prompt admission and selection",measuredMilliseconds(data?.admissionMs)),
        DiagnosticLine(if(session==null) "Runtime pipeline wall (excludes session initialization/UI)" else "Session ask wall (includes lazy initialization; excludes queue/session construction/UI)",measuredMilliseconds(trace.totalMs)),
        DiagnosticLine("This query's lazy initialization",measuredMilliseconds(trace.initializationMs)),
        DiagnosticLine("Model loaded in this session",if(session==null) "Unknown" else (session.generator!=null).toString()),
        DiagnosticLine("Generator constructor hash verification and load",measuredMilliseconds(session?.generatorLoadAndVerificationMs)),
        DiagnosticLine("ONNX/tokenizer constructors initialized",session?.embedderInitialized?.toString() ?: "Unknown"),
        DiagnosticLine("Returned candidate pool",data?.candidates?.size?.toString() ?: "Not returned"))
}
fun candidateSelection(trace:RuntimeTrace,key:String):String {
    val plan=trace.selection ?: return "Selection not reached"
    return if(key in plan.keys) "Selected" else plan.decisions.lastOrNull { it.key==key }?.reason ?: "Not selected"
}
