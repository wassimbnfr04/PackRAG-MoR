package org.packrag.model

import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class EvidenceSelectionTest {
    @Test fun twentyEightFixedSelectionPlansAndCallerReversal() {
        val cases=JSONObject(File(System.getProperty("packrag.repo"),"product/tests/fixtures/selection-contracts.json").readText()).getJSONArray("cases")
        assertEquals(28,cases.length())
        for(i in 0 until cases.length()) {
            val case=cases.getJSONObject(i);val rows=case.getJSONArray("items")
            val labels=(0 until rows.length()).associate { index -> val row=rows.getJSONObject(index)
                row.getString("key") to (row.optString("source",row.getString("key")) to row.optString("canonical",row.getString("key"))) }
            val items=(0 until rows.length()).map { index -> val row=rows.getJSONObject(index);val key=row.getString("key")
                val required=row.optJSONArray("required")
                SelectionItem(key,row.optInt("position",index+1),labels.getValue(key),row.optString("source",key),
                    SelectionValue(0,row.optDouble("value",-row.optInt("position",index+1).toDouble()),0,.8),row.optString("context","same"),
                    if(required==null) emptyList() else (0 until required.length()).map { val name=required.getString(it);labels[name] ?: (name to name) },
                    row.optBoolean("resolved",true)) }
            fun run(pool:List<SelectionItem>)=EvidenceSelection.select(pool,case.optInt("chunk_cap",4),1200,1536) { keys ->
                val cost=case.optJSONObject("costs")?.optJSONArray(keys.joinToString(","))
                if(cost==null) keys.size*100 to keys.size*100+100 else cost.getInt(0) to cost.getInt(1) }
            for(pool in listOf(items,items.reversed())) {
                val result=runCatching { run(pool) }
                if(case.has("error")) {
                    assertEquals(case.getString("id"),case.getString("error"),(result.exceptionOrNull() as SelectionFailure).state)
                    if(case.getString("error") in listOf("INCOMPLETE_LEGAL_CONFLICT_EVIDENCE","LEGAL_CONFLICT_UNRESOLVED")) {
                        val plan=requireNotNull((result.exceptionOrNull() as SelectionFailure).selection)
                        assertEquals(case.getString("error"),plan.admission);assertTrue(plan.keys.isEmpty() && plan.sources.isEmpty())
                        assertEquals(items.map { it.key }.toSet(),plan.decisions.map { it.key }.toSet())
                    }
                } else {
                    val plan=result.getOrThrow();val expected=case.getJSONArray("selected")
                    assertEquals(case.getString("id"),(0 until expected.length()).map { expected.getString(it) },plan.keys)
                    assertEquals(items.map { it.key }.toSet(),plan.decisions.map { it.key }.toSet())
                    val reasons=case.optJSONObject("reasons")
                    if(reasons!=null) for(key in reasons.keys()) assertEquals(reasons.getString(key),plan.decisions.single { it.key==key }.reason)
                    assertEquals(run(items),plan)
                }
            }
        }
    }
    @Test fun negativeWholeTrialCostsReject() {
        val item=SelectionItem("a",1,"s" to "t","s",SelectionValue(0,1.0,0,.8),"")
        for(cost in listOf(-1 to 100,100 to -1)) {
            val failure=assertThrows(SelectionFailure::class.java) { EvidenceSelection.select(listOf(item),4,1200,1536) { cost } }
            assertEquals("INVALID_SELECTION_COST",failure.state)
        }
    }
}
