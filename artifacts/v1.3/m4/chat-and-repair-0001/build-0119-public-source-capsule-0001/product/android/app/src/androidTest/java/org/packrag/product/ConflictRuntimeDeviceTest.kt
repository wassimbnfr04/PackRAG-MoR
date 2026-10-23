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
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.model.Query
import org.packrag.packs.ActivePack

/** Real LFM on synthetic conflict inputs; isolated explicit test trust, not legal gold. */
@RunWith(AndroidJUnit4::class)
class ConflictRuntimeDeviceTest {
    @Test fun actualConflictRejectionsAndAuthoritySupersessionExceptionAnswers() {
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext;val assets=instrument.context.assets
        val reference=assets.open("conflict-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val keyRows=reference.getJSONArray("public_keys")
        val keys=(0 until keyRows.length()).map { i -> val row=keyRows.getJSONObject(i)
            assets.open("conflict-corpus/"+row.getString("filename")).use { it.readBytes() }.also { assertEquals(row.getString("sha256"),Crypto.sha256(it)) } }
        val root=File(context.filesDir,"conflict-runtime-${UUID.randomUUID()}");assertTrue(root.mkdirs());val results=JSONArray()
        try {
            ProductSession(context,File(root,"registry"),keys,true).use { session ->
                val records=linkedMapOf<String,ActivePack>();val rows=reference.getJSONArray("packs")
                for(i in 0 until rows.length()) {
                    val row=rows.getJSONObject(i);val archive=File(root,row.getString("filename"))
                    assets.open("conflict-corpus/"+archive.name).use { source -> archive.outputStream().use { source.copyTo(it) } }
                    assertEquals(row.getString("sha256"),Crypto.fileHash(archive));records[row.getString("id")]=session.registry.activate(archive)
                }
                val cases=reference.getJSONArray("cases")
                for(label in listOf("UNKNOWN","DIFFERENT_CURATORS","BEFORE_CAP","FIVE_COMPANIONS","AUTHORITY","SUPERSEDES_CURRENT","EXCEPTION")) {
                    session.registry.snapshot().toList().forEach { session.registry.deactivate(it.id) }
                    val case=(0 until cases.length()).map { cases.getJSONObject(it) }.single { it.getString("id")==label }
                    val names=conflictStrings(case.getJSONArray("packs"))
                    for(name in names) { val pack=records.getValue(name);session.registry.activateInstalled(pack.id,pack.version) }
                    assertEquals(names.map { records.getValue(it).id }.toSet(),session.registry.snapshot().map { it.id }.toSet())
                    val trace=session.ask(Query(case.getString("raw"),case.getString("as_of"),conflictNullable(case,"jurisdiction")))
                    val guarded=label in listOf("UNKNOWN","DIFFERENT_CURATORS","BEFORE_CAP","FIVE_COMPANIONS")
                    if(guarded) {
                        assertEquals(label,if(label=="FIVE_COMPANIONS") "INCOMPLETE_LEGAL_CONFLICT_EVIDENCE" else "IDENTIFIER_AMBIGUOUS",trace.answer.state)
                        assertNull(trace.answer.text);assertEquals(0,trace.emittedTokens);assertEquals(0,trace.prefillTokens);assertTrue(trace.selected.isEmpty())
                    } else {
                        assertEquals(label,"ANSWER_ACCEPTED",trace.answer.state)
                        assertTrue(label,trace.answer.text!!.contains("74 °C"));assertFalse(trace.answer.text!!.contains("68 °C"));assertFalse(trace.answer.text!!.contains("</think>"))
                        assertTrue(trace.answer.sources.isNotEmpty())
                        assertTrue(trace.answer.sources.any { it.canonicalText=="The Aster-9 thermal controller has a maximum continuous operating temperature of 74 °C." })
                        assertTrue(trace.answer.sources.all { source -> source.conflicts.isNotEmpty() && source.conflicts.all { it.resolved } })
                        assertEquals(if(label=="EXCEPTION") 2 else 1,trace.selected.size)
                        assertTrue(trace.prefillTokens<=1536 && trace.evidenceTokens<=1200 && trace.emittedTokens in 1..512)
                    }
                    results.put(JSONObject().put("id",label).put("status","PASS").put("state",trace.answer.state).put("answer",trace.answer.text ?: JSONObject.NULL)
                        .put("actual_weight_inference",!guarded).put("model_load_not_excluded",guarded).put("selected",JSONArray(trace.selected))
                        .put("prefill_tokens",trace.prefillTokens).put("evidence_tokens",trace.evidenceTokens).put("emitted_tokens_including_terminal",trace.emittedTokens)
                        .put("total_ms_including_lazy_initialization",trace.totalMs).put("initialization_ms",trace.initializationMs)
                        .put("prefill_ms",trace.prefillMs ?: JSONObject.NULL).put("decode_wall_ms",trace.decodeWallMs ?: JSONObject.NULL)
                        .put("sources",JSONArray(trace.answer.sources.map { source -> JSONObject().put("id",source.evidenceId).put("canonical_text",source.canonicalText)
                            .put("pack_id",source.pack.packId).put("version",source.pack.version).put("manifest_sha256",source.pack.manifestSha256)
                            .put("conflict_states",JSONArray(source.conflicts.map { it.state })) })))
                    File(context.filesDir,"m4-conflict-runtime-progress.json").writeText(JSONObject().put("status","RUNNING").put("cases",results).toString(2),Charsets.UTF_8)
                }
            }
            File(context.filesDir,"m4-conflict-runtime.json").writeText(JSONObject().put("status","PASS").put("cases",results).put("raw_reasoning_persisted",false)
                .put("purpose","ACTUAL_LFM_SYNTHETIC_CONFLICT_RUNTIME_NOT_LEGAL_REVIEW_CALIBRATION_OR_PERFORMANCE")
                .put("developer_trust","EXPLICIT_ISOLATED_TEST_KEYS_NOT_PRODUCTION_DEFAULT").put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET").toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));root.deleteRecursively() }
    }
}
