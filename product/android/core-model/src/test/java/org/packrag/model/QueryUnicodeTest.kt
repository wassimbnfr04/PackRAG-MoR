package org.packrag.model

import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class QueryUnicodeTest {
    @Test fun officialUnicode15ConformanceAndSharedQueryCases() {
        val root=File(requireNotNull(System.getProperty("packrag.repo")))
        var count=0
        File(root,"product/tests/unicode15/NormalizationTest.txt").forEachLine { raw ->
            val line=raw.substringBefore('#').trim()
            if(line.isNotEmpty() && !line.startsWith("@")) {
                val columns=line.split(';').take(5).map { field -> buildString { field.trim().split(Regex("\\s+")).filter { it.isNotEmpty() }.forEach { appendCodePoint(it.toInt(16)) } } }
                for(column in columns) assertEquals("row $count",columns[3],QueryUnicode.nfkc(column))
                count++
            }
        }
        assertEquals(19074,count)
        val reference=JSONObject(File(root,"product/tests/query-unicode-cases.json").readText())
        assertEquals(reference.getString("table_sha256"),QueryUnicode.TABLE_SHA256)
        val cases=reference.getJSONArray("cases")
        for(i in 0 until cases.length()) { val case=cases.getJSONObject(i); assertEquals(case.getString("id"),case.getString("normalized"),normalizeQuery(case.getString("raw"))) }
    }
}
