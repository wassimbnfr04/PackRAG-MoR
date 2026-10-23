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
import org.packrag.crypto.ApprovedPublishers
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.model.Query

/** Production core policy in a debug artifact; actual production build policy is a separate gate. */
@RunWith(AndroidJUnit4::class)
class ReleaseTrustCoreDeviceTest {
    @Test fun approvedPublicStoreRejectsUnknownAndUncalibratedAndRetainsActualRuntime() {
        val instrument=InstrumentationRegistry.getInstrumentation(); val context=instrument.targetContext; val assets=instrument.context.assets
        val corpus=assets.open("release-trust-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val approved=context.assets.open("release-trust.json").use { it.readBytes() }
        assertEquals(corpus.getString("approved_store_sha256"),Crypto.sha256(approved))
        val keys=ProductConfiguration.keys(context,false); assertEquals(1,keys.size)
        val dev=assets.open("developer-public-key.raw").use { it.readBytes() }
        assertFalse(keys.any { it.contentEquals(dev) })
        val stores=assets.open("release-trust-corpus/store-cases.json").bufferedReader().use { JSONArray(it.readText()) }
        val storeResults=JSONArray()
        for(i in 0 until stores.length()) {
            val case=stores.getJSONObject(i)
            val failure=runCatching { ApprovedPublishers.keys(case.getJSONObject("value").toString().toByteArray()) }.exceptionOrNull()
            if(case.getBoolean("accept")) assertNull(case.getString("id"),failure) else assertNotNull(case.getString("id"),failure)
            storeResults.put(JSONObject().put("id",case.getString("id")).put("passed",true))
        }
        val root=File(context.filesDir,"release-trust-core-${UUID.randomUUID()}"); assertTrue(root.mkdirs())
        val cases=corpus.getJSONArray("cases"); val results=JSONArray()
        try {
            ProductSession(context,File(root,"registry"),keys,false).use { session ->
                var accepted: org.packrag.packs.ActivePack? = null
                var original: Map<String,String>? = null
                for(i in 0 until cases.length()) {
                    val case=cases.getJSONObject(i); val input=File(root,case.getString("filename"))
                    assets.open("release-trust-corpus/"+input.name).use { source -> input.outputStream().use { source.copyTo(it) } }
                    assertEquals(case.getString("sha256"),Crypto.fileHash(input))
                    if(case.getBoolean("accept_production")) {
                        val installed=session.registry.activate(input); accepted=installed
                        assertEquals(case.getString("manifest_sha256"),installed.manifestHash)
                        original=installed.root.walkTopDown().filter { it.isFile }.associate { it.relativeTo(installed.root).path to Crypto.fileHash(it) }
                    } else {
                        val failure=runCatching { session.registry.activate(input) }.exceptionOrNull()
                        assertNotNull(case.getString("id"),failure)
                        assertTrue(case.getString("id")+": "+failure,failure!!.message.orEmpty().contains(case.getString("error_contains")))
                        val previous=requireNotNull(accepted)
                        assertEquals(listOf(previous.id+"@"+previous.version),session.registry.snapshot().map { it.id+"@"+it.version })
                        assertEquals(original,previous.root.walkTopDown().filter { it.isFile }.associate { it.relativeTo(previous.root).path to Crypto.fileHash(it) })
                        assertTrue(File(root,"registry/.staging").listFiles()!!.isEmpty())
                    }
                    assertEquals(case.getString("sha256"),Crypto.fileHash(input))
                    results.put(JSONObject().put("id",case.getString("id")).put("passed",true).put("accept_production",case.getBoolean("accept_production")))
                }
                val input=File(root,"development.kpack")
                assets.open("walking-skeleton.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
                val failure=runCatching { session.registry.activate(input) }.exceptionOrNull()
                assertNotNull(failure); assertTrue(failure!!.message.orEmpty().contains("Unknown signer or invalid signature"))
                val trace=session.ask(Query("What is the maximum continuous operating temperature of the Aster-9?","2026-10-06"))
                assertEquals("ANSWER_ACCEPTED",trace.answer.state); assertTrue(trace.answer.text.orEmpty().contains("74 °C") && trace.answer.text.orEmpty().contains("[S1]"))
                assertFalse(trace.answer.text.orEmpty().contains("</think>"))
                assertEquals("The Aster-9 thermal controller has a maximum continuous operating temperature of 74 °C.",trace.answer.sources.single().canonicalText)
                assertEquals(requireNotNull(accepted).manifestHash,trace.answer.sources.single().pack.manifestSha256)
                val validity=requireNotNull(trace.answer.sources.single().validity)
                assertTrue(validity.sourceStartUnknown && validity.sourceEndUnknown && validity.chunkStartInherits && validity.chunkEndInherits)
                assertNull(validity.effectiveFrom); assertNull(validity.effectiveUntilExcl); assertFalse(validity.emptyIntersection)
                val metadata=requireNotNull(trace.answer.sources.single().metadata)
                assertEquals(requireNotNull(accepted).manifest.getJSONObject("publisher").getString("key_id"),metadata.publisherKeyId)
                assertNull(metadata.authorityRank);assertNull(metadata.documentVersion);assertNull(metadata.issuedAt);assertNull(metadata.article)
                assertTrue(metadata.relations.isEmpty())
                assertTrue(trace.prefillTokens<=1536 && trace.evidenceTokens<=1200 && trace.emittedTokens in 1..512)
                File(context.filesDir,"m3-release-trust-core.json").writeText(JSONObject().put("status","PASS").put("cases",results).put("store_cases",storeResults)
                    .put("development_signer_rejected",true).put("prior_active_hashes_preserved",true).put("failed_staging_cleaned",true)
                    .put("actual_weight_inference",true).put("answer",trace.answer.text).put("canonical_source",trace.answer.sources.single().canonicalText)
                    .put("unknown_open_validity_provenance_checked",true)
                    .put("authenticated_source_metadata_checked",true)
                    .put("total_ms_including_lazy_initialization",trace.totalMs).put("emitted_tokens_including_terminal",trace.emittedTokens)
                    .put("limits","Production core policy tested inside DEBUG artifact. Positive pack contains synthetic schema-only calibration, not measured calibration or source authority. Actual release build policy and final release acceptance remain separate.")
                    .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET").toString(2),Charsets.UTF_8)
            }
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator)); root.deleteRecursively() }
    }
}
