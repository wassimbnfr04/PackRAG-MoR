package org.packrag.model
import java.io.File
import java.security.MessageDigest
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class SourceTextTest {
    @Test fun fixedPresenceAllScalarsAndBlankResolverFields() {
        val fixed=JSONObject(File(System.getProperty("packrag.repo"),"product/tests/fixtures/source-text-contracts.json").readText())
        val cases=fixed.getJSONArray("cases");assertEquals(38,cases.length())
        for(i in 0 until cases.length()) { val row=cases.getJSONObject(i)
            assertEquals(row.getString("id"),row.getBoolean("expected_nonblank"),SourceText.nonBlank(if(row.isNull("value")) null else row.getString("value"))) }
        val values=fixed.getJSONArray("whitespace_points");val whitespace=(0 until values.length()).map { values.getInt(it) }.toSet();assertEquals(29,whitespace.size)
        var count=0
        for(point in 0..0x10ffff) { if(point in 0xd800..0xdfff)continue
            assertEquals("U+${point.toString(16)}",point !in whitespace,SourceText.nonBlank(String(Character.toChars(point))));count++ }
        assertEquals(1112064,count)
        fun hash(text:String)=MessageDigest.getInstance("SHA-256").digest(text.toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it) }
        for(point in whitespace) for(field in listOf("canonical","text","derivation_source","reviewer_id")) {
            val blank=String(Character.toChars(point));val canonical=if(field=="canonical") blank else "Source."
            val body=if(field=="text") blank else "74 °C."
            val row=DerivedText("c","generator","en",body,hash(body),"human_reviewed_translation",if(field=="derivation_source") blank else "SYNTHETIC",if(field=="reviewer_id") blank else "SYNTHETIC","2026-10-09")
            val result=runCatching { GeneratorRepresentations.select(canonical,hash(canonical),if(field=="canonical") "en" else "fr",listOf(row)) }
            assertEquals(field+":"+point,"INVALID_GENERATOR_PROVENANCE",(result.exceptionOrNull() as RepresentationFailure).state)
        }
    }
}
