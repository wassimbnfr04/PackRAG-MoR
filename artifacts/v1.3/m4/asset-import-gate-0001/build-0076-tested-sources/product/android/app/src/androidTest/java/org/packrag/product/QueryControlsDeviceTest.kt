package org.packrag.product

import android.app.Application
import android.net.Uri
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

/** Actual app orchestration; isolated registry, built-in publisher trust and pinned assets. */
@RunWith(AndroidJUnit4::class)
class QueryControlsDeviceTest {
    private val instrument get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrument.targetContext
    private fun guardedFiles():Map<String,String> = LocalAssetImportTestSupport.ownerGuard()
    private fun waitReady(model:PackRagViewModel) {
        val end = System.nanoTime()+600_000_000_000L
        while(model.state.value.busy && System.nanoTime()<end) android.os.SystemClock.sleep(20)
        assertFalse("Query action timed out",model.state.value.busy)
    }
    private fun generatorInitialized(model:PackRagViewModel):Boolean {
        // Test-only read of the actual private session, no injected generator or production test hook.
        val field=PackRagViewModel::class.java.getDeclaredField("session");field.isAccessible=true
        return (field.get(model) as ProductSession?)?.generatorLoadAndVerificationMs != null
    }
    private fun withModel(resultName:String,body:(PackRagViewModel,JSONArray)->Unit) {
        val before=guardedFiles();val store=ViewModelStore();val root=File(context.filesDir,"query-controls-${UUID.randomUUID()}")
        lateinit var model:PackRagViewModel
        val cases=JSONArray()
        try {
            instrument.runOnMainSync { model=PackRagViewModel(context.applicationContext as Application,root);store.put("test",model) };waitReady(model)
            body(model,cases)
            assertEquals(before,guardedFiles())
            File(context.filesDir,resultName).writeText(JSONObject().put("status","PASS").put("cases",cases)
                .put("owner_registry_and_model_sha256",JSONObject(before)).put("owner_guard_scope","EXPLICIT_50_PUBLIC_BASELINE_FILES_NO_ENUMERATION").put("guards_unchanged",true)
                .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET").put("raw_reasoning_persisted",false)
                .put("limits","Functional actual-application controls and synthetic walking fixture; not final content, real legal review, held-out gold or performance benchmark.").toString(2),Charsets.UTF_8)
        } finally {
            instrument.runOnMainSync { store.clear() }
            val end=System.nanoTime()+10_000_000_000L
            var released=false
            while(!released && System.nanoTime()<end) {
                released=runCatching { ProductSession(context,root,ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS).use { };true }.getOrDefault(false)
                if(!released) android.os.SystemClock.sleep(50)
            }
            check(released);require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));root.deleteRecursively()
        }
    }
    @Test fun invalidAndNoPackInputsDoNotInitializeNativeGeneration() = withModel("m4-ui-query-inputs.json") { model,cases ->
        fun submit(text:String,date:String,code:String="",current:Boolean=false) {
            instrument.runOnMainSync { model.ask(text,date,code,current) };waitReady(model)
        }
        val invalid=listOf(
            Triple("question","2027-02-29","INVALID_QUERY_DATE"),Triple("question","2026-04-31","INVALID_QUERY_DATE"),
            Triple("\uD800","2026-10-10","INVALID_QUERY_TEXT"),Triple("\u0085","2026-10-10","EMPTY_QUESTION"))
        for((text,date,expected) in invalid) {
            submit(text,date);assertEquals("INVALID_QUERY",model.state.value.answer?.state);assertEquals(expected,model.state.value.inputError)
            assertNull(model.state.value.submission);assertNull(model.state.value.trace);assertFalse(generatorInitialized(model))
            cases.put(JSONObject().put("id",expected+"-"+cases.length()).put("passed",true).put("generator_initialized",false))
        }
        submit("question","2028-02-29","ma")
        assertEquals("INVALID_QUERY_JURISDICTION",model.state.value.inputError);assertFalse(generatorInitialized(model))
        cases.put(JSONObject().put("id","lowercase-code-not-corrected").put("passed",true))
        submit("raw question","2028-02-29","MA-01",true)
        assertEquals("NO_ACTIVE_PACK",model.state.value.answer?.state);assertFalse(generatorInitialized(model))
        val captured=requireNotNull(model.state.value.submission)
        assertEquals("raw question",captured.query.raw);assertEquals("2028-02-29",captured.query.asOf);assertEquals("MA-01",captured.query.jurisdiction);assertTrue(captured.query.currentLaw)
        assertTrue(captured.packs.isEmpty());assertEquals("NO_ACTIVE_PACK",model.state.value.trace?.answer?.state)
        cases.put(JSONObject().put("id","no-pack-keeps-submission-no-generator").put("passed",true))
        instrument.runOnMainSync { model.cancel() }
        assertEquals("CANCELLED",model.state.value.answer?.state);assertNull(model.state.value.submission);assertNull(model.state.value.trace)
        cases.put(JSONObject().put("id","cancel-clears-captured-context-and-trace").put("passed",true))
    }
    @Test fun actualStaleAnswerOwnsContextJurisdictionExcludesAndPackChangeClearsIt() = withModel("m4-ui-query-runtime.json") { model,cases ->
        val input=File(context.cacheDir,"query-controls-${UUID.randomUUID()}.kpack")
        val question="What is the maximum continuous operating temperature of the Aster-9?"
        fun submit(code:String="") { instrument.runOnMainSync { model.ask(question,"2027-01-01",code,true) };waitReady(model) }
        try {
            instrument.context.assets.open("walking-skeleton.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
            instrument.runOnMainSync { model.importPack(Uri.fromFile(input)) };waitReady(model)
            assertNull(model.state.value.answer);assertNull(model.state.value.submission);assertNull(model.state.value.trace)
            submit()
            val state=model.state.value;val trace=requireNotNull(state.trace);val captured=requireNotNull(state.submission)
            assertEquals("ANSWER_ACCEPTED",trace.answer.state);assertTrue(trace.answer.text!!.contains("74 °C"));assertTrue(trace.answer.text!!.contains("[S1]"))
            assertEquals("2027-01-01",captured.query.asOf);assertTrue(captured.query.currentLaw);assertNull(captured.query.jurisdiction)
            assertEquals(captured.query,trace.evidenceContext?.query);assertEquals(captured.packs.map { it.identity },trace.evidenceContext?.identities)
            assertEquals(1,captured.packs.size);assertTrue(captured.packs.single().advisoryAt(captured.query.asOf))
            val source=trace.answer.sources.single()
            assertEquals("The Aster-9 thermal controller has a maximum continuous operating temperature of 74 °C.",source.canonicalText)
            assertEquals(captured.packs.single().identity,source.pack);assertEquals(Crypto.sha256(source.canonicalText.toByteArray(Charsets.UTF_8)),source.canonicalTextSha256)
            assertFalse(trace.answer.text!!.contains("</think>"))
            cases.put(JSONObject().put("id","stale-advisory-real-cited-answer").put("passed",true).put("state",trace.answer.state).put("answer",trace.answer.text)
                .put("as_of",captured.query.asOf).put("jurisdiction",JSONObject.NULL).put("current_law",true)
                .put("manifest_sha256",source.pack.manifestSha256).put("canonical_text",source.canonicalText).put("canonical_sha256",source.canonicalTextSha256)
                .put("prefill_tokens",trace.prefillTokens).put("evidence_tokens",trace.evidenceTokens).put("emitted_tokens",trace.emittedTokens)
                .put("session_wall_ms_including_lazy_initialization",trace.totalMs).put("initialization_ms",trace.initializationMs))
            submit("MA")
            assertEquals("NO_RELEVANT_EVIDENCE",model.state.value.answer?.state);assertEquals(0,model.state.value.trace?.emittedTokens)
            assertEquals("MA",model.state.value.submission?.query?.jurisdiction);assertNull(model.state.value.answer?.text)
            // The old accepted context remains an independent immutable value.
            assertNull(captured.query.jurisdiction);assertEquals("2027-01-01",captured.query.asOf)
            cases.put(JSONObject().put("id","exact-jurisdiction-excludes-unknown-source-no-generation").put("passed",true))
            instrument.runOnMainSync { model.ask(question,"2028-02-29");model.cancel() }
            assertEquals("CANCELLED",model.state.value.answer?.state);assertNull(model.state.value.trace);assertNull(model.state.value.submission)
            submit()
            assertEquals("ANSWER_ACCEPTED",model.state.value.answer?.state)
            cases.put(JSONObject().put("id","cancel-and-real-recovery-keeps-new-context").put("passed",true))
            val id=captured.packs.single().identity.packId
            instrument.runOnMainSync { model.deactivate(id) };waitReady(model)
            assertNull(model.state.value.answer);assertNull(model.state.value.trace);assertNull(model.state.value.submission);assertTrue(model.state.value.activeFreshness.isEmpty())
            cases.put(JSONObject().put("id","pack-mutation-clears-old-result-context-and-advisory").put("passed",true))
        } finally { input.delete() }
    }
}
