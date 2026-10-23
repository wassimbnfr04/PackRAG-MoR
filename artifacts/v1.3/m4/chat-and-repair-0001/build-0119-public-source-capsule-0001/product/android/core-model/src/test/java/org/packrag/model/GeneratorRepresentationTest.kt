package org.packrag.model

import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class GeneratorRepresentationTest {
    @Test fun thirtyTwoIndependentlyFixedRepresentationContracts() {
        val cases=JSONObject(File(System.getProperty("packrag.repo"),"product/tests/fixtures/representation-contracts.json").readText()).getJSONArray("cases")
        assertEquals(32,cases.length())
        fun nullable(row:JSONObject,key:String):String?=if(row.isNull(key)) null else row.getString(key)
        for(i in 0 until cases.length()) {
            val case=cases.getJSONObject(i);val source=case.getJSONObject("canonical");val rows=case.getJSONArray("derived")
            val derived=(0 until rows.length()).map { j -> val r=rows.getJSONObject(j)
                DerivedText(r.getString("chunk_id"),r.getString("purpose"),r.getString("language"),r.getString("text"),r.getString("text_sha256"),
                    r.getString("derivation_method"),nullable(r,"derivation_source"),nullable(r,"reviewer_id"),nullable(r,"reviewed_at")) }
            for(values in listOf(derived,derived.reversed())) {
                val result=runCatching { GeneratorRepresentations.select(source.getString("canonical_text"),source.getString("text_sha256"),source.getString("language"),values) }
                if(!case.isNull("error")) {
                    assertTrue(case.getString("id"),result.isFailure)
                    assertEquals(case.getString("id"),case.getString("error"),(result.exceptionOrNull() as RepresentationFailure).state)
                } else {
                    val e=case.getJSONObject("expected")
                    val expected=GeneratorRepresentation(e.getString("text"),e.getString("language"),e.getString("text_sha256"),e.getString("derivation_method"),
                        nullable(e,"derivation_source"),nullable(e,"reviewer_id"),nullable(e,"reviewed_at"),e.getString("canonical_language"),e.getString("canonical_text_sha256"))
                    assertEquals(case.getString("id"),expected,result.getOrThrow())
                }
            }
        }
    }
}
