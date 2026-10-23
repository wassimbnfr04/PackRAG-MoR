package org.packrag.product

import android.app.Application
import android.net.Uri
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.file.Files
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.model.PackOverview
import org.packrag.model.Query

@RunWith(AndroidJUnit4::class)
class PackOverviewDeviceTest {
    private val instrument get()=InstrumentationRegistry.getInstrumentation()
    private val context get()=instrument.targetContext
    private val fixtureName get()=if(BuildConfig.ALLOW_DEVELOPMENT_PACKS) "walking-skeleton.kpack" else "release-trust-corpus/calibration-schema-only.kpack"
    private fun expected()=instrument.context.assets.open("pack-overview-corpus/expectations.json").bufferedReader().use {
        JSONObject(it.readText()).getJSONObject("fixtures").getJSONObject(fixtureName)
    }
    private fun fixture(root:File):File=File(root,"input.kpack").also { file ->
        instrument.context.assets.open(fixtureName).use { source -> file.outputStream().use { source.copyTo(it) } }
        assertEquals(expected().getString("transport_sha256"),Crypto.fileHash(file))
    }
    private fun checked(value:PackOverview,expect:JSONObject) {
        assertEquals(expect.getString("pack_id"),value.identity.packId);assertEquals(expect.getString("version"),value.identity.version)
        assertEquals(expect.getString("manifest_sha256"),value.identity.manifestSha256)
        assertEquals(expect.getString("name"),value.name);assertEquals(expect.getString("publisher_name"),value.publisherName)
        assertEquals(expect.getString("publisher_key_id"),value.publisherKeyId);assertEquals(expect.getString("update_check_after"),value.updateCheckAfter)
        assertEquals(expect.getLong("manifest_bytes"),value.manifestBytes);assertEquals(expect.getLong("payload_bytes"),value.payloadBytes)
        assertEquals(expect.getLong("transport_bytes"),value.transportBytes)
    }
    private fun ready(model:PackRagViewModel) {
        val end=System.nanoTime()+600_000_000_000L
        while(model.state.value.busy && System.nanoTime()<end)android.os.SystemClock.sleep(20)
        assertFalse("ViewModel operation timed out",model.state.value.busy)
    }
    private fun clear(store:ViewModelStore,root:File) {
        instrument.runOnMainSync { store.clear() }
        val end=System.nanoTime()+10_000_000_000L;var released=false
        while(!released && System.nanoTime()<end) {
            released=runCatching { ProductSession(context,root,ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS).use { };true }.getOrDefault(false)
            if(!released)android.os.SystemClock.sleep(50)
        }
        check(released);LocalAssetImportTestSupport.deleteOwned(root,"pack-overview-")
    }
    private fun record(name:String,cases:JSONArray,before:Map<String,String>,extra:JSONObject=JSONObject()) {
        assertEquals(before,LocalAssetImportTestSupport.ownerGuard())
        File(context.filesDir,name).writeText(extra.put("status","PASS").put("variant",BuildConfig.BUILD_TYPE)
            .put("cases",cases).put("owner_registry_and_model_sha256",JSONObject(before))
            .put("owner_guard_scope","EXPLICIT_50_PUBLIC_BASELINE_FILES_NO_ENUMERATION").put("raw_reasoning_persisted",false)
            .put("limits","Synthetic verified overview/runtime controls; approved fixture tests calibration schema only. No owner content, radio isolation, normal performance or full F3/M4/release acceptance.").toString(2),Charsets.UTF_8)
    }
    @Test fun verifiedMetadataAndRealAnswerRemainOwnedThroughReadOnlyInspection() {
        val before=LocalAssetImportTestSupport.ownerGuard();val root=File(context.filesDir,"pack-overview-${UUID.randomUUID()}");assertTrue(root.mkdir())
        val store=ViewModelStore();val cases=JSONArray();lateinit var model:PackRagViewModel
        fun passed(id:String){cases.put(JSONObject().put("id",id).put("passed",true))}
        try {
            val expect=expected();val input=fixture(root)
            ProductSession(context,root,ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS).use { it.registry.activate(input) }
            instrument.runOnMainSync { model=PackRagViewModel(context.applicationContext as Application,root);store.put("overview",model) };ready(model)
            val row=model.state.value.installed.single();assertTrue(row.active);checked(requireNotNull(authenticatedOverview(row)),expect)
            passed("actual-active-reverified-publisher-identity-and-three-byte-domains")
            instrument.runOnMainSync { model.ask("What is the maximum continuous operating temperature of the Aster-9?","2027-01-01","",true) };ready(model)
            val completed=model.state.value;val answer=requireNotNull(completed.answer);val trace=requireNotNull(completed.trace)
            assertEquals("ANSWER_ACCEPTED",answer.state);assertTrue(answer.text!!.contains("74 °C") && answer.text!!.contains("[S1]"));assertFalse(answer.text!!.contains("</think>"))
            assertEquals(row.identity,answer.sources.single().pack)
            assertEquals("266af80f5d4da1dac500acd9a2bcc1fd2317b2caf49141ebb586280b9df49333",answer.sources.single().canonicalTextSha256)
            assertTrue(trace.diagnostics!!.generationCalled && trace.emittedTokens in 1..512);assertNotNull(trace.session!!.generator)
            passed("actual-pinned-native-cited-answer-and-canonical-identity")
            instrument.runOnMainSync { model.inspectPack(row.id,row.version,row.hash) };ready(model)
            val inspected=model.state.value;assertEquals(row.identity,inspected.details!!.identity)
            assertSame(answer,inspected.answer);assertSame(trace,inspected.trace);assertSame(completed.submission,inspected.submission);assertEquals(completed.completedResultId,inspected.completedResultId)
            checked(requireNotNull(inspected.installed.single().overview),expect)
            passed("read-only-details-reinspection-preserves-owned-completed-context")
            instrument.runOnMainSync { model.deactivate(row.id) };ready(model)
            assertTrue(model.state.value.packs.isEmpty());assertFalse(model.state.value.installed.single().active);checked(requireNotNull(model.state.value.installed.single().overview),expect)
            instrument.runOnMainSync { model.ask("Aster-9 temperature?","2027-01-01","",true) };ready(model)
            assertEquals("NO_ACTIVE_PACK",model.state.value.answer?.state);assertEquals(0,model.state.value.trace!!.emittedTokens)
            assertEquals("ANSWER_ACCEPTED",answer.state);passed("inactive-overview-does-not-activate-and-no-active-skips-generation")
            assertEquals(before,LocalAssetImportTestSupport.ownerGuard());passed("explicit-fifty-owner-public-files-unchanged")
            record("m4-pack-overview-runtime.json",cases,before,JSONObject().put("actual_weight_inference",true).put("answer",answer.text)
                .put("emitted_tokens",trace.emittedTokens).put("completed_result_id",completed.completedResultId).put("fixture_sha256",expect.getString("transport_sha256")))
        } finally { clear(store,root) }
    }
    @Test fun wrongAndTamperedInactiveIdentitiesExposeNoStaleVerifiedMetadata() {
        val before=LocalAssetImportTestSupport.ownerGuard();val root=File(context.filesDir,"pack-overview-${UUID.randomUUID()}");assertTrue(root.mkdir())
        val store=ViewModelStore();val cases=JSONArray();lateinit var model:PackRagViewModel
        var changed:File?=null;var original:ByteArray?=null
        fun passed(id:String){cases.put(JSONObject().put("id",id).put("passed",true))}
        try {
            val expect=expected();val input=fixture(root)
            ProductSession(context,root,ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS).use { session ->
                assertTrue(session.registry.installed().isEmpty())
                val empty=session.ask(Query("overview empty check","2027-01-01",null,false))
                assertEquals("NO_ACTIVE_PACK",empty.answer.state);assertNull(empty.session!!.generator);assertFalse(empty.session!!.embedderInitialized)
                passed("empty-overview-state-does-not-initialize-models")
                val installed=session.registry.activate(input);session.registry.deactivate(installed.id)
                checked(session.registry.overview(installed.id,installed.version,installed.manifestHash),expect)
                assertTrue(session.registry.snapshot().isEmpty());passed("independent-verified-inactive-overview")
                for(request in listOf(Triple("org.missing.pack",installed.version,installed.manifestHash),
                    Triple(installed.id,"99.0.0",installed.manifestHash),Triple(installed.id,installed.version,"0".repeat(64)))) {
                    val result=runCatching { session.registry.overview(request.first,request.second,request.third) }
                    assertTrue(result.isFailure);assertTrue(session.registry.snapshot().isEmpty())
                }
                passed("missing-wrong-id-version-hash-rejected-without-activation")
            }
            instrument.runOnMainSync { model=PackRagViewModel(context.applicationContext as Application,root);store.put("negative",model) };ready(model)
            instrument.runOnMainSync { model.ask("No active pack?","2027-01-01","",false) };ready(model)
            val completed=model.state.value;assertEquals("NO_ACTIVE_PACK",completed.answer?.state);assertNull(completed.trace!!.session!!.generator)
            val row=completed.installed.single();checked(requireNotNull(row.overview),expect);assertFalse(row.active)
            val db=File(root,"packs/${row.id}/${row.version}/knowledge.sqlite")
            require(db.canonicalPath.startsWith(root.canonicalPath+File.separator));assertFalse(Files.isSymbolicLink(db.toPath()));assertTrue(db.isFile)
            changed=db;original=db.readBytes();db.appendBytes(byteArrayOf(0))
            instrument.runOnMainSync { model.inspectPack(row.id,row.version,row.hash) };ready(model)
            val rejected=model.state.value;assertNull(rejected.details);assertNotNull(rejected.detailsError)
            val unavailable=rejected.installed.single();assertNull(unavailable.overview);assertFalse(unavailable.active);assertTrue(rejected.packs.isEmpty())
            assertEquals(1,packOverviewLines(unavailable,"2027-01-01").size)
            assertFalse(packOverviewLines(unavailable,"2027-01-01").any { it.contains(expect.getString("publisher_name")) || it.startsWith("Payload bytes") })
            assertSame(completed.answer,rejected.answer);assertSame(completed.trace,rejected.trace);assertSame(completed.submission,rejected.submission);assertEquals(completed.completedResultId,rejected.completedResultId)
            passed("tampered-inactive-overview-unavailable-with-no-stale-metadata-or-context-loss")
            db.writeBytes(requireNotNull(original));original=null
            instrument.runOnMainSync { model.inspectPack(row.id,row.version,row.hash) };ready(model)
            val restored=model.state.value;checked(requireNotNull(restored.installed.single().overview),expect);assertNotNull(restored.details)
            assertFalse(restored.installed.single().active);assertTrue(restored.packs.isEmpty())
            assertSame(completed.answer,restored.answer);assertSame(completed.trace,restored.trace);assertEquals(completed.completedResultId,restored.completedResultId)
            passed("restored-test-owned-payload-explicitly-reverifies-without-activation")
            assertEquals(before,LocalAssetImportTestSupport.ownerGuard());passed("explicit-fifty-owner-public-files-unchanged")
            record("m4-pack-overview-negative.json",cases,before,JSONObject().put("no_native_initialization_in_negative_method",true)
                .put("completed_result_id",completed.completedResultId).put("fixture_sha256",expect.getString("transport_sha256")))
        } finally { original?.let { bytes -> changed?.writeBytes(bytes) };clear(store,root) }
    }
}
