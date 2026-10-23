package org.packrag.product

import android.app.Application
import androidx.lifecycle.ViewModelStore
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

@RunWith(AndroidJUnit4::class)
class SourceDetailsViewModelTest {
    @Test fun actualAnswerContextSurvivesInspectionAndMutationClearsDetails() {
        assertTrue(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext
        val root=File(context.filesDir,"source-detail-model-${UUID.randomUUID()}");val store=ViewModelStore()
        val input=File(context.cacheDir,"source-detail-${UUID.randomUUID()}.kpack")
        fun guard():Map<String,String> = LocalAssetImportTestSupport.ownerGuard()
        val before=guard();lateinit var model:PackRagViewModel;val cases=JSONArray()
        fun ready() { val end=System.nanoTime()+600_000_000_000L;while(model.state.value.busy && System.nanoTime()<end) android.os.SystemClock.sleep(20);assertFalse(model.state.value.busy);assertNotEquals("RUNTIME_ERROR",model.state.value.answer?.state) }
        fun passed(name:String) { cases.put(JSONObject().put("id",name).put("passed",true)) }
        try {
            instrument.context.assets.open("walking-skeleton.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
            ProductSession(context,root,ProductConfiguration.keys(context),true).use { it.registry.activate(input) }
            instrument.runOnMainSync { model=PackRagViewModel(context.applicationContext as Application,root);store.put("model",model) };ready()
            instrument.runOnMainSync { model.ask("What is the maximum continuous operating temperature of the Aster-9?","2027-01-01","",true) };ready()
            val state=model.state.value;val answer=requireNotNull(state.answer);val trace=requireNotNull(state.trace);val submission=requireNotNull(state.submission)
            assertEquals("ANSWER_ACCEPTED",answer.state);val record=answer.sources.single();assertEquals("CC0-1.0",record.attribution?.license)
            assertEquals("2026-10-05",record.attribution?.retrievedAt);assertNull(record.attribution?.canonicalUri);assertTrue(record.attribution!!.redistributionAllowed!!)
            assertEquals(record.attribution,record.originRecords.single().chunk.attribution)
            val pack=state.installed.single()
            instrument.runOnMainSync { model.inspectPack(pack.id,pack.version,pack.hash) };ready()
            assertSame(answer,model.state.value.answer);assertSame(trace,model.state.value.trace);assertSame(submission,model.state.value.submission)
            assertEquals(record.pack,model.state.value.details?.identity);assertEquals(10,model.state.value.details?.sources?.size)
            passed("actual-cited-answer-attribution-and-captured-context-survive-active-inspection")
            instrument.runOnMainSync { model.closeDetails() }
            assertNull(model.state.value.details);assertNull(model.state.value.detailRequest);assertSame(answer,model.state.value.answer)
            passed("closing-details-retains-original-answer")
            instrument.runOnMainSync { model.deactivate(pack.id) };ready()
            assertNull(model.state.value.answer);assertNull(model.state.value.trace);assertNull(model.state.value.submission);assertNull(model.state.value.details)
            instrument.runOnMainSync { model.inspectPack(pack.id,pack.version,pack.hash) };ready()
            assertNotNull(model.state.value.details);assertTrue(model.state.value.packs.isEmpty());assertNull(model.state.value.trace)
            passed("inactive-inspection-does-not-activate-or-reuse-old-answer")
            instrument.runOnMainSync { model.inspectPack(pack.id,pack.version,"0".repeat(64)) };ready()
            assertEquals("PACK_DETAIL_VERIFICATION_FAILED",model.state.value.message);assertNotNull(model.state.value.detailsError);assertNull(model.state.value.details)
            assertTrue(model.state.value.packs.isEmpty());assertEquals(1,model.state.value.installed.size)
            passed("wrong-requested-identity-fails-without-verified-details-or-mutation")
            assertEquals(before,guard());passed("explicit-fifty-owner-public-files-unchanged")
            File(context.filesDir,"m4-source-details-viewmodel.json").writeText(JSONObject().put("status","PASS").put("cases",cases)
                .put("actual_weight_inference",true).put("prefill_tokens",trace.prefillTokens).put("evidence_tokens",trace.evidenceTokens).put("emitted_tokens",trace.emittedTokens)
                .put("session_wall_ms_including_lazy_initialization",trace.totalMs).put("initialization_ms",trace.initializationMs)
                .put("owner_registry_and_model_sha256",JSONObject(before)).put("owner_guard_scope","EXPLICIT_50_PUBLIC_BASELINE_FILES_NO_ENUMERATION").put("raw_reasoning_persisted",false)
                .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET").toString(2),Charsets.UTF_8)
        } finally {
            instrument.runOnMainSync { store.clear() };input.delete();val end=System.nanoTime()+10_000_000_000L;var released=false
            while(!released && System.nanoTime()<end) {
                released=runCatching { ProductSession(context,root,ProductConfiguration.keys(context),true).use { };true }.getOrDefault(false)
                if(!released) android.os.SystemClock.sleep(50)
            }
            check(released);require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));assertTrue(root.deleteRecursively())
        }
    }
}
