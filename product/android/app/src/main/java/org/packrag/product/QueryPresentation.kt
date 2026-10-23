package org.packrag.product

import org.packrag.model.PackIdentity
import org.packrag.model.Query
import org.packrag.model.TemporalDates
import org.packrag.model.ownedList

/** Form input uses the existing runtime contract; no hidden date/code correction. */
fun submittedQuery(question: String, asOf: String, jurisdiction: String, currentLaw: Boolean): Query =
    Query(question, asOf, jurisdiction.takeUnless { it.isEmpty() }, currentLaw)

/** Values copied from an authenticated active manifest; no live JSONObject is retained. */
data class PackFreshness(val identity: PackIdentity, val updateCheckAfter: String) {
    init { TemporalDates.date(updateCheckAfter) }
    fun advisoryAt(asOf: String): Boolean { TemporalDates.date(asOf); return asOf >= updateCheckAfter }
}

class SubmittedQuery(val query: Query, packs: List<PackFreshness>) {
    val packs = ownedList(packs)
}

fun queryInputGuidance(code: String): String = when(code) {
    "INVALID_QUERY_DATE" -> "Enter a valid calendar date as YYYY-MM-DD. Check the device clock if using today's date."
    "INVALID_QUERY_JURISDICTION" -> "Leave jurisdiction empty for all, or enter an uppercase code such as MA or MA-01."
    "EMPTY_QUESTION" -> "Enter a question."
    "INVALID_QUERY_TEXT" -> "The question contains invalid Unicode text. Replace it and try again."
    else -> "Check the question, date and jurisdiction, then try again."
}

fun answerGuidance(state: String): String = when(state) {
    "ANSWER_ACCEPTED" -> "Answer passed output and citation-format checks. Open a citation to inspect the evidence; these checks do not prove every claim is supported."
    "NO_ACTIVE_PACK" -> "Import and activate a verified knowledge pack, then ask again."
    "NO_RELEVANT_EVIDENCE" -> "No relevant evidence was admitted for this question and its date/jurisdiction. Check those controls or use another verified pack."
    "INSUFFICIENT_EVIDENCE" -> "The model reported insufficient evidence. Try a more specific question or another verified pack."
    "OUTPUT_REJECTED" -> "The generated answer failed output or citation validation. No candidate answer is shown. Rephrase the question or inspect the pack."
    "IDENTIFIER_AMBIGUOUS" -> "The identifier matches more than one source. Add a distinguishing identifier or select the appropriate packs."
    "INVALID_QUERY" -> "Correct the form input before asking again."
    "CANCELLED" -> "The request was cancelled. You can ask another question."
    "RUNTIME_ERROR" -> "The request could not finish. Check local assets and verified packs, then try again."
    else -> "The request could not produce an accepted answer ($state). Check the question and verified packs."
}
