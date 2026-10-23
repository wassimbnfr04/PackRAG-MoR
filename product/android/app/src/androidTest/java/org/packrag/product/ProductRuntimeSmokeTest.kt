package org.packrag.product

import android.content.pm.PackageManager
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
import org.packrag.runtime.RuntimeTrace

/** Retained real pipeline gate independent of interactive UI availability; not a benchmark. */
@RunWith(AndroidJUnit4::class)
class ProductRuntimeSmokeTest {
    @Test fun retainedVerifiedRetrievalToActualGeneratorAndCanonicalSource() {
        val instrument=InstrumentationRegistry.getInstrumentation(); val context=instrument.targetContext; val assets=instrument.context.assets
        assertFalse(context.packageManager.getPackageInfo(context.packageName,PackageManager.GET_PERMISSIONS).requestedPermissions?.contains("android.permission.INTERNET") ?: false)
        val key=assets.open("developer-public-key.raw").use { it.readBytes() }
        val root=File(context.filesDir,"runtime-smoke-${UUID.randomUUID()}"); assertTrue(root.mkdirs()); val archive=File(root,"input.kpack")
        assets.open("walking-skeleton.kpack").use { source -> archive.outputStream().use { source.copyTo(it) } }
        val results=JSONArray()
        fun record(id:String,trace:RuntimeTrace,passed:Boolean) {
            results.put(JSONObject().put("id",id).put("passed",passed).put("state",trace.answer.state).put("answer",trace.answer.text ?: JSONObject.NULL)
                .put("selected",JSONArray(trace.selected)).put("prefill_tokens",trace.prefillTokens).put("evidence_tokens",trace.evidenceTokens).put("emitted_tokens_including_terminal",trace.emittedTokens)
                .put("total_ms_including_lazy_initialization",trace.totalMs).put("initialization_ms",trace.initializationMs)
                .put("prefill_ms",trace.prefillMs ?: JSONObject.NULL).put("decode_wall_ms",trace.decodeWallMs ?: JSONObject.NULL)
                .put("sources",JSONArray(trace.answer.sources.map { s -> JSONObject().put("id",s.evidenceId).put("canonical_text",s.canonicalText).put("pack_id",s.pack.packId).put("version",s.pack.version).put("manifest_sha256",s.pack.manifestSha256) })))
            File(context.filesDir,"runtime-smoke-progress.json").writeText(JSONObject().put("status","RUNNING").put("cases",results).toString(2),Charsets.UTF_8)
            assertTrue("Retained runtime smoke failed: $id ${trace.answer.state}",passed)
        }
        try {
            ProductSession(context,File(root,"registry"),listOf(key),true).use { session ->
                val absent=session.ask(Query("Aster-9 temperature limit?","2026-10-05")); record("NO_PACK",absent,absent.answer.state=="NO_ACTIVE_PACK"); assertNull(session.generatorLoadAndVerificationMs)
                val pack=session.registry.activate(archive)
                val trace=session.ask(Query("What is the maximum continuous operating temperature of the Aster-9?","2026-10-05"))
                record("SUPPORTED_REAL_INFERENCE",trace,trace.answer.state=="ANSWER_ACCEPTED" && trace.answer.text?.contains("74 °C")==true && trace.answer.text?.contains("[S1]")==true && trace.answer.text?.contains("</think>")!=true)
                assertEquals("The Aster-9 thermal controller has a maximum continuous operating temperature of 74 °C.",trace.answer.sources.single().canonicalText)
                assertEquals(pack.manifestHash,trace.answer.sources.single().pack.manifestSha256)
                val validity=requireNotNull(trace.answer.sources.single().validity)
                assertTrue(validity.sourceStartUnknown && validity.sourceEndUnknown && validity.chunkStartInherits && validity.chunkEndInherits)
                assertNull(validity.effectiveFrom); assertNull(validity.effectiveUntilExcl); assertFalse(validity.emptyIntersection)
                val metadata=requireNotNull(trace.answer.sources.single().metadata)
                assertEquals(pack.manifest.getJSONObject("publisher").getString("key_id"),metadata.publisherKeyId)
                assertNull(metadata.authorityRank);assertNull(metadata.documentVersion);assertNull(metadata.issuedAt);assertNull(metadata.article)
                assertTrue(metadata.relations.isEmpty())
                assertTrue(trace.prefillTokens<=1536 && trace.evidenceTokens<=1200 && trace.selected.size<=4 && trace.emittedTokens in 1..512)
                val unrelated=session.ask(Query("Describe a rainbow dragon","2026-10-05")); record("UNRELATED",unrelated,unrelated.answer.state=="NO_RELEVANT_EVIDENCE" && unrelated.emittedTokens==0 && unrelated.answer.text==null)
                File(context.filesDir,"product-runtime-smoke.json").writeText(JSONObject().put("status","PASS").put("cases",results).put("actual_weight_inference",true).put("canonical_source_checked",true)
                    .put("purpose","RETAINED_PRODUCT_PIPELINE_SMOKE_NOT_INTERACTIVE_OR_RELEASE_BENCHMARK").put("raw_reasoning_persisted",false)
                    .put("unknown_open_validity_provenance_checked",true)
                    .put("authenticated_source_metadata_checked",true)
                    .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET").toString(2),Charsets.UTF_8)
            }
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator)); root.deleteRecursively() }
    }
}
