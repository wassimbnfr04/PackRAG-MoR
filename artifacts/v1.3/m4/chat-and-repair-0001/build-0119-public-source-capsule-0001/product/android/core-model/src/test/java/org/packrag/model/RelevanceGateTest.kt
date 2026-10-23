package org.packrag.model

import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class RelevanceGateTest {
    @Test fun thirtyTwoIndependentMergedPoolAdmissionExpectations() {
        val cases=JSONObject(File(System.getProperty("packrag.repo"),"product/tests/fixtures/relevance-contracts.json").readText()).getJSONArray("cases")
        assertEquals(32,cases.length())
        for(i in 0 until cases.length()) {
            val case=cases.getJSONObject(i);val rows=case.getJSONArray("signals")
            val signals=(0 until rows.length()).map { j -> val row=rows.getJSONObject(j)
                RelevanceSignal(row.getBoolean("exact"),if(row.isNull("sparse_rank")) null else row.getInt("sparse_rank"),
                    if(row.isNull("dense_rank")) null else row.getInt("dense_rank"),row.getDouble("dense_score"),row.getBoolean("calibrated"),
                    if(row.isNull("agreed_threshold")) null else row.getDouble("agreed_threshold"),
                    if(row.isNull("dense_only_threshold")) null else row.getDouble("dense_only_threshold")) }
            val expected=case.getJSONArray("expected")
            assertEquals(case.getString("id"),(0 until expected.length()).map { expected.getBoolean(it) },RelevanceGate.mark(signals))
        }
    }
}
