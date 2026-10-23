package org.packrag.model

import java.io.File
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class ConflictContractTest {
    @Test fun fortyIndependentFixedContractsAndCallerOrderAreShared() {
        val file=File(System.getProperty("packrag.repo"),"product/tests/fixtures/conflict-contracts.json")
        val cases=JSONObject(file.readText()).getJSONArray("cases");assertEquals(40,cases.length())
        fun nullable(row:JSONObject,key:String)=if(row.isNull(key)) null else row.getString(key)
        fun strings(array:JSONArray)=(0 until array.length()).map { array.getString(it) }
        for(index in 0 until cases.length()) {
            val case=cases.getJSONObject(index);val rows=case.getJSONArray("nodes")
            val nodes=(0 until rows.length()).map { i -> val row=rows.getJSONObject(i)
                ConflictNode(row.getString("key"),row.getString("original"),row.getString("text"),row.getString("domain"),
                    row.getString("publisher_key"),nullable(row,"jurisdiction"),nullable(row,"canonical_uri"),nullable(row,"article"),
                    if(row.isNull("authority")) null else row.getInt("authority"),row.getInt("order")) }
            val links=case.getJSONArray("edges")
            val edges=(0 until links.length()).map { i -> val row=links.getJSONObject(i)
                ConflictEdge(row.getString("source"),row.getString("target"),row.getString("kind"),row.getString("provenance"),row.getDouble("confidence")) }
            val actual=Conflicts.resolve(nodes,edges);val expected=case.getJSONArray("expected")
            assertEquals(case.getString("id"),expected.length(),actual.size)
            for(i in actual.indices) {
                val row=expected.getJSONObject(i);val required=row.getJSONArray("required")
                val result=ConflictDecision(strings(row.getJSONArray("members")),row.getString("state"),row.getString("reason"),
                    nullable(row,"preferred"),strings(row.getJSONArray("retained")),(0 until required.length()).map { j ->
                        val pair=required.getJSONArray(j);pair.getString(0) to pair.getString(1) })
                assertEquals(case.getString("id"),result,actual[i])
            }
            assertEquals(case.getString("id"),actual,Conflicts.resolve(nodes.reversed(),edges.reversed()))
            if(!case.isNull("alias_keys")) assertEquals(case.getString("id"),case.getBoolean("expected_alias_resolved"),
                Conflicts.resolvedInterpretation(strings(case.getJSONArray("alias_keys")).toSet(),actual))
        }
    }
}
