package org.packrag.model

import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class QueryContractTest {
    @Test fun sharedStrictQueryScalarWordAndAliasContracts() {
        val root=File(requireNotNull(System.getProperty("packrag.repo")))
        val data=JSONObject(File(root,"product/tests/query-contract-cases.json").readText())
        val cases=data.getJSONArray("query_cases")
        for(i in 0 until cases.length()) {
            val case=cases.getJSONObject(i)
            val outcome=runCatching { Query(case.getString("raw"),case.getString("as_of"),if(case.isNull("jurisdiction")) null else case.getString("jurisdiction"),case.getBoolean("current_law")) }
            if(case.getBoolean("accept")) { assertTrue(case.getString("id"),outcome.isSuccess); assertEquals(case.getString("raw"),outcome.getOrThrow().raw) }
            else { assertTrue(case.getString("id"),outcome.isFailure); assertEquals(case.getString("error"),outcome.exceptionOrNull()!!.message) }
        }
        val words=data.getJSONArray("word_cases")
        for(i in 0 until words.length()) {
            val case=words.getJSONObject(i); val expected=case.getJSONArray("terms")
            assertEquals((0 until expected.length()).map { expected.getString(it) },QueryUnicode.wordTerms(normalizeQuery(case.getString("raw"))))
        }
        val aliases=data.getJSONArray("alias_cases")
        for(i in 0 until aliases.length()) { val case=aliases.getJSONObject(i); assertEquals(case.getBoolean("matched"),QueryUnicode.containsAlias(normalizeQuery(case.getString("text")),normalizeQuery(case.getString("alias")))) }
    }
}
