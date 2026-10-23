package org.packrag.product

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.model.Query

/** Actual runtime, isolated developer registry; no final benchmark claim. */
@RunWith(AndroidJUnit4::class)
class QueryIdentifierRuntimeDeviceTest {
    @Test fun crossPackAmbiguityAbstainsBeforeGenerationAndExpiredCollisionRetainsRealAnswer() {
        val instrument=InstrumentationRegistry.getInstrumentation(); val context=instrument.targetContext; val assets=instrument.context.assets
        val public=assets.open("query-identifier-corpus/public-key.raw").use { it.readBytes() }
        val root=File(context.filesDir,"query-runtime-${UUID.randomUUID()}"); assertTrue(root.mkdirs())
        val results=JSONArray()
        try {
            ProductSession(context,File(root,"registry"),listOf(public),true).use { session ->
                val records=linkedMapOf<String,org.packrag.packs.ActivePack>()
                for(name in listOf("primary","collision","expired")) {
                    val archive=File(root,"$name.kpack")
                    assets.open("query-identifier-corpus/$name.kpack").use { source -> archive.outputStream().use { source.copyTo(it) } }
                    records[name]=session.registry.activate(archive)
                }
                val raw=" Ａｓｔｅｒ－９ operating temperature "
                val query=Query(raw,"2026-10-06"); val rejected=session.ask(query)
                assertEquals("IDENTIFIER_AMBIGUOUS",rejected.answer.state); assertNull(rejected.answer.text)
                assertEquals(0,rejected.emittedTokens); assertEquals(0,rejected.prefillTokens); assertTrue(rejected.selected.isEmpty())
                assertEquals(raw,query.raw); assertEquals("aster-9 operating temperature",query.normalized)
                results.put(JSONObject().put("id","AMBIGUOUS_NO_GENERATION").put("status","PASS").put("state",rejected.answer.state).put("emitted_tokens",rejected.emittedTokens)
                    .put("prefill_tokens",rejected.prefillTokens).put("model_load_not_excluded",true))
                session.registry.deactivate(records.getValue("collision").id)
                val trace=session.ask(Query("What is the maximum continuous operating temperature of the Aster-9?","2026-10-06"))
                assertEquals("ANSWER_ACCEPTED",trace.answer.state); assertTrue(trace.answer.text!!.contains("74 °C")); assertTrue(trace.answer.text!!.contains("[S1]"))
                assertEquals("The Aster-9 thermal controller has a maximum continuous operating temperature of 74 °C.",trace.answer.sources.single().canonicalText)
                assertEquals(records.getValue("primary").manifestHash,trace.answer.sources.single().pack.manifestSha256)
                assertTrue(trace.prefillTokens<=1536 && trace.evidenceTokens<=1200 && trace.selected.size<=4 && trace.emittedTokens in 1..512)
                results.put(JSONObject().put("id","EXPIRED_COLLISION_REAL_SUPPORTED").put("status","PASS").put("state",trace.answer.state).put("answer",trace.answer.text)
                    .put("selected",JSONArray(trace.selected)).put("prefill_tokens",trace.prefillTokens).put("evidence_tokens",trace.evidenceTokens)
                    .put("emitted_tokens_including_terminal",trace.emittedTokens).put("total_ms",trace.totalMs).put("prefill_ms",trace.prefillMs).put("decode_wall_ms",trace.decodeWallMs))
            }
            File(context.filesDir,"m4-query-identifier-runtime.json").writeText(JSONObject().put("status","PASS").put("purpose","ACTUAL_QUERY_ALIAS_RUNTIME_NOT_RELEASE_CALIBRATION_OR_PERFORMANCE")
                .put("cases",results).put("raw_reasoning_persisted",false).put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET").toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator)); root.deleteRecursively() }
    }
}
