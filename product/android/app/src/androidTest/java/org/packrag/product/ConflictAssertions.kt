package org.packrag.product

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.packrag.model.ConflictNode
import org.packrag.model.ConflictEdge
import org.packrag.model.ConflictDecision
import org.packrag.model.Conflicts

internal fun conflictNullable(row:JSONObject,key:String)=if(row.isNull(key)) null else row.getString(key)
internal fun conflictStrings(array:JSONArray)=(0 until array.length()).map { array.getString(it) }
internal fun expectedConflict(row:JSONObject):ConflictDecision {
    val required=row.getJSONArray("required")
    return ConflictDecision(conflictStrings(row.getJSONArray("members")),row.getString("state"),row.getString("reason"),
        conflictNullable(row,"preferred"),conflictStrings(row.getJSONArray("retained")),(0 until required.length()).map { i ->
            val pair=required.getJSONArray(i);pair.getString(0) to pair.getString(1) })
}
internal fun assertFixedConflictCases(cases:JSONArray) {
    assertEquals(40,cases.length())
    for(index in 0 until cases.length()) {
        val case=cases.getJSONObject(index);val rows=case.getJSONArray("nodes")
        val nodes=(0 until rows.length()).map { i -> val row=rows.getJSONObject(i)
            ConflictNode(row.getString("key"),row.getString("original"),row.getString("text"),row.getString("domain"),row.getString("publisher_key"),
                conflictNullable(row,"jurisdiction"),conflictNullable(row,"canonical_uri"),conflictNullable(row,"article"),
                if(row.isNull("authority")) null else row.getInt("authority"),row.getInt("order")) }
        val links=case.getJSONArray("edges")
        val edges=(0 until links.length()).map { i -> val row=links.getJSONObject(i)
            ConflictEdge(row.getString("source"),row.getString("target"),row.getString("kind"),row.getString("provenance"),row.getDouble("confidence")) }
        val expected=case.getJSONArray("expected")
        val actual=Conflicts.resolve(nodes,edges)
        assertEquals(case.getString("id"),(0 until expected.length()).map { expectedConflict(expected.getJSONObject(it)) },actual)
        assertEquals(case.getString("id"),actual,Conflicts.resolve(nodes.reversed(),edges.reversed()))
        if(!case.isNull("alias_keys")) assertEquals(case.getString("id"),case.getBoolean("expected_alias_resolved"),
            Conflicts.resolvedInterpretation(conflictStrings(case.getJSONArray("alias_keys")).toSet(),actual))
    }
}
