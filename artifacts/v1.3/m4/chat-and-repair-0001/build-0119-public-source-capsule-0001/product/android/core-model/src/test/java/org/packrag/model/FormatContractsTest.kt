package org.packrag.model

import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class FormatContractsTest {
    @Test fun sharedLanguageTemporalAndWhitespaceCases() {
        val root = File(requireNotNull(System.getProperty("packrag.repo")))
        val cases = JSONObject(File(root,"product/tests/format-cases.json").readText())
        val languages=cases.getJSONArray("languages")
        for(i in 0 until languages.length()) { val case=languages.getJSONArray(i); assertEquals(case.getString(0),case.getBoolean(1),LanguageTags.valid(case.getString(0))) }
        for(group in listOf("dates","timestamps")) {
            val groupCases=cases.getJSONArray(group)
            for(i in 0 until groupCases.length()) { val case=groupCases.getJSONArray(i); val failure=runCatching { if(group=="dates") TemporalDates.date(case.getString(0)) else TemporalDates.utc(case.getString(0)) }.exceptionOrNull()
                if(case.getBoolean(1)) assertNull(case.getString(0)+": "+failure,failure) else assertNotNull(case.getString(0),failure) }
        }
        val normalized=cases.getJSONArray("normalization")
        for(i in 0 until normalized.length()) { val case=normalized.getJSONArray(i); assertEquals(case.getString(1),normalizeQuery(case.getString(0))) }
    }
}
