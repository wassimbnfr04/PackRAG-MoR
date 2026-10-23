package org.packrag.runtime
import org.packrag.generator.QuoteProtocol

data class ValidatedOutput(val state: String, val text: String? = null, val citations: List<String> = emptyList(), val reason: String? = null)

object OutputValidator {
    fun validate(buffer: String, supplied: Set<String>, truncated: Boolean = false,quoteUnits:List<String>?=null): ValidatedOutput {
        if (truncated || Regex("</think>").findAll(buffer).count() != 1)
            return ValidatedOutput("GENERATION_UNUSABLE", reason = "unfinished_reasoning_or_truncated")
        val final = buffer.substringAfter("</think>").trim()
        if (final.isEmpty() || "<think>" in final || "<|" in final)
            return ValidatedOutput("GENERATION_UNUSABLE", reason = "empty_or_malformed_final")
        if (final == "INSUFFICIENT_EVIDENCE") return ValidatedOutput("INSUFFICIENT_EVIDENCE")
        val citations = Regex("\\[S[^\\]\\n]*\\]").findAll(final).map { it.value.substring(1, it.value.length - 1) }.distinct().toList()
        if (citations.isEmpty() || citations.any { !Regex("S[1-9]\\d*").matches(it) || it !in supplied })
            return ValidatedOutput("OUTPUT_REJECTED", reason = "missing_or_unknown_citation")
        if ("[S" in final.replace(Regex("\\[S[1-9]\\d*\\]"), ""))
            return ValidatedOutput("OUTPUT_REJECTED", reason = "malformed_citation")
        if (final.split(Regex("\n\\s*\n")).any { !Regex("\\[S[1-9]\\d*\\]").containsMatchIn(it) })
            return ValidatedOutput("OUTPUT_REJECTED", reason = "uncited_paragraph")
        if(quoteUnits!=null && !QuoteProtocol.matches(final,quoteUnits))
            return ValidatedOutput("OUTPUT_REJECTED",reason="quote_not_from_selected_evidence")
        return ValidatedOutput("ANSWER_ACCEPTED", final, citations)
    }
}
