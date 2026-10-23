package org.packrag.model

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class ValidityContractTest {
    private fun nullable(row:JSONObject,key:String):String?=if(row.isNull(key)) null else row.getString(key)
    private fun chunk(row:JSONObject)=Chunk("c","s","title","source",null,"locator","text","hash","hash",0,
        nullable(row,"jurisdiction"),nullable(row,"source_from"),nullable(row,"source_until"),nullable(row,"effective_from"),
        nullable(row,"effective_until_excl"),nullable(row,"legal_status"),"publisher",null,"en")
    private fun values(v:ValidityProvenance)=mapOf(
        "source_from" to v.sourceFrom,"source_until_excl" to v.sourceUntilExcl,"chunk_from" to v.chunkFrom,"chunk_until_excl" to v.chunkUntilExcl,
        "effective_from" to v.effectiveFrom,"effective_until_excl" to v.effectiveUntilExcl,"source_start_unknown" to v.sourceStartUnknown,
        "source_end_unknown" to v.sourceEndUnknown,"chunk_start_inherits" to v.chunkStartInherits,"chunk_end_inherits" to v.chunkEndInherits,
        "empty_intersection" to v.emptyIntersection,"jurisdiction" to v.jurisdiction,"legal_status" to v.legalStatus)
    @Test fun sharedSignedIntervalSemanticsAndFixedProvenance() {
        val data=javaClass.getResourceAsStream("/validity-cases.json")!!.bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val cases=data.getJSONArray("cases")
        for(i in 0 until cases.length()) {
            val case=cases.getJSONObject(i);val query=Query("question",case.getString("as_of"),nullable(case,"jurisdiction"),case.getBoolean("current_law"))
            assertEquals(case.getString("id"),case.getBoolean("eligible"),eligible(chunk(case.getJSONObject("row")),query))
        }
        val provenance=data.getJSONArray("provenance_cases")
        for(i in 0 until provenance.length()) {
            val case=provenance.getJSONObject(i);val expected=case.getJSONObject("expected")
            val actual=values(validityProvenance(chunk(case.getJSONObject("row"))))
            assertEquals(expected.length(),actual.size)
            for((key,value) in actual) assertEquals(case.getString("id")+":"+key,if(expected.isNull(key)) null else expected.get(key),value)
        }
    }
}
