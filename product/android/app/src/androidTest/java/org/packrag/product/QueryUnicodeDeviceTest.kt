package org.packrag.product

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.text.Normalizer
import org.json.JSONObject
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.model.QueryUnicode
import org.packrag.model.normalizeQuery

@RunWith(AndroidJUnit4::class)
class QueryUnicodeDeviceTest {
    @Test fun officialUnicode15AndDesktopQueryParity() {
        val instrument=InstrumentationRegistry.getInstrumentation()
        val assets=instrument.context.assets
        var count=0
        assets.open("unicode15/NormalizationTest.txt").bufferedReader(Charsets.UTF_8).useLines { lines -> lines.forEach { raw ->
            val line=raw.substringBefore('#').trim()
            if(line.isNotEmpty() && !line.startsWith("@")) {
                val columns=line.split(';').take(5).map { field -> buildString { field.trim().split(Regex("\\s+")).filter { it.isNotEmpty() }.forEach { appendCodePoint(it.toInt(16)) } } }
                for(column in columns) assertEquals("row $count",columns[3],QueryUnicode.nfkc(column))
                count++
            }
        } }
        assertEquals(19074,count)
        val reference=assets.open("query-unicode-cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        assertEquals(reference.getString("table_sha256"),QueryUnicode.TABLE_SHA256)
        val cases=reference.getJSONArray("cases"); val results=JSONArray()
        for(i in 0 until cases.length()) {
            val case=cases.getJSONObject(i); val raw=case.getString("raw")
            val actual=normalizeQuery(raw)
            assertEquals(case.getString("id"),case.getString("normalized"),actual)
            results.put(JSONObject().put("id",case.getString("id")).put("normalized",actual).put("status","PASS"))
        }
        // This is a read-only OS-normalizer observation in this new build, not
        // a relabelled execution of the historical APK or exhaustive OS audit.
        val probe=String(Character.toChars(0x1e030))
        val output=JSONObject().put("status","PASS").put("unicode_version",QueryUnicode.VERSION)
            .put("table_sha256",QueryUnicode.TABLE_SHA256).put("official_rows",count).put("official_comparisons",count*5)
            .put("query_cases",results).put("os_nfkc_u1e030_observed",Normalizer.normalize(probe,Normalizer.Form.NFKC))
            .put("frozen_nfkc_u1e030",QueryUnicode.nfkc(probe)).put("mobile_data_policy","REMAINS_ON_NO_AIRPLANE_ACCEPTANCE")
        File(instrument.targetContext.filesDir,"m4-query-unicode.json").writeText(output.toString(2),Charsets.UTF_8)
    }
}
