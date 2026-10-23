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
import org.packrag.generator.GeneratorBackend

/** Actual ViewModel/native replacement and cancellation, no substituted output. */
@RunWith(AndroidJUnit4::class)
class DiagnosticLifecycleDeviceTest {
    @Test fun nativeReplacementCancelRecoveryInspectionAndMutationKeepResultOwnership() {
        assertTrue(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext
        fun guard():Map<String,String> = listOf("packs","production-registry","models").flatMap { name ->
            val folder=File(context.filesDir,name);if(!folder.exists()) emptyList() else folder.walkTopDown().filter { it.isFile }
                .map { it.relativeTo(context.filesDir).path to Crypto.fileHash(it) }.toList()
        }.toMap()
        val before=guard();val store=ViewModelStore();val root=File(context.filesDir,"diagnostic-lifecycle-${UUID.randomUUID()}")
        val input=File(context.cacheDir,"diagnostic-lifecycle-${UUID.randomUUID()}.kpack");val cases=JSONArray()
        lateinit var model:PackRagViewModel
        fun passed(id:String) { cases.put(JSONObject().put("id",id).put("passed",true)) }
        fun ready() {
            val end=System.nanoTime()+600_000_000_000L
            while(model.state.value.busy && System.nanoTime()<end) android.os.SystemClock.sleep(20)
            assertFalse("Action timed out",model.state.value.busy);assertNotEquals("RUNTIME_ERROR",model.state.value.answer?.state)
        }
        fun generating():Boolean {
            val field=PackRagViewModel::class.java.getDeclaredField("session");field.isAccessible=true
            val session=field.get(model) as ProductSession? ?: return false
            val backend=ProductSession::class.java.getDeclaredField("generator");backend.isAccessible=true
            return (backend.get(session) as GeneratorBackend?)?.isGenerating==true
        }
        fun waitGeneration() {
            val end=System.nanoTime()+180_000_000_000L
            while(!generating() && model.state.value.busy && System.nanoTime()<end) android.os.SystemClock.sleep(10)
            assertTrue("Must observe real native entry, not only a busy initialization",generating())
            assertTrue(model.state.value.busy);assertNull(model.state.value.answer);assertNull(model.state.value.trace)
            assertNull(model.state.value.completedResultId)
        }
        val question="What is the maximum continuous operating temperature of the Aster-9?"
        try {
            instrument.runOnMainSync { model=PackRagViewModel(context.applicationContext as Application,root);store.put("test",model) };ready()
            instrument.context.assets.open("walking-skeleton.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
            assertEquals("19da286b9f0860c312dc8d14ce0ee8681bf12ca092a7b8a12171fd86abe02c7f",Crypto.fileHash(input))
            instrument.runOnMainSync { model.importPack(Uri.fromFile(input)) };ready()
            instrument.runOnMainSync { model.ask(question,"2027-01-01") };waitGeneration()
            val originalSubmission=requireNotNull(model.state.value.submission)
            val replacement="For the Aster-9, what is the maximum continuous operating temperature?"
            instrument.runOnMainSync { model.ask(replacement,"2028-02-29","MA",true) };ready()
            val replaced=model.state.value;val replacementId=requireNotNull(replaced.completedResultId)
            assertFalse(generating());assertEquals("NO_RELEVANT_EVIDENCE",replaced.answer?.state)
            assertEquals(replacement,replaced.submission!!.query.raw);assertEquals("MA",replaced.submission!!.query.jurisdiction)
            assertEquals(replaced.submission!!.query,replaced.trace!!.diagnostics!!.context.query)
            assertFalse(replaced.trace!!.diagnostics!!.generationCalled);assertTrue(replaced.trace!!.diagnostics!!.candidates!!.isEmpty())
            assertEquals(0,replaced.trace!!.emittedTokens);assertNull(replaced.answer!!.text)
            assertEquals(question,originalSubmission.query.raw);assertNull(originalSubmission.query.jurisdiction)
            passed("replacement-observed-during-native-generation-discards-original-and-keeps-only-new-context")
            instrument.runOnMainSync { model.ask(question,"2027-01-01") };waitGeneration()
            instrument.runOnMainSync { model.cancel() }
            assertEquals("CANCELLED",model.state.value.answer?.state);assertNull(model.state.value.trace)
            assertNull(model.state.value.submission);assertNull(model.state.value.completedResultId)
            val end=System.nanoTime()+30_000_000_000L
            while(generating() && System.nanoTime()<end) android.os.SystemClock.sleep(10)
            assertFalse("Native cancellation did not finish",generating())
            assertEquals("CANCELLED",model.state.value.answer?.state);assertNull(model.state.value.trace)
            passed("real-native-cancel-clears-completed-trace-submission-navigation-and-stays-cleared")
            instrument.runOnMainSync { model.ask(question,"2027-01-01") };ready()
            val captured=model.state.value;val trace=requireNotNull(captured.trace);val id=requireNotNull(captured.completedResultId)
            assertNotEquals(replacementId,id);assertEquals("ANSWER_ACCEPTED",trace.answer.state)
            assertTrue(trace.answer.text!!.contains("74 °C"));assertTrue(trace.answer.text!!.contains("[S1]"))
            assertFalse(trace.answer.text!!.contains("</think>"));assertEquals(captured.submission!!.query,trace.diagnostics!!.context.query)
            assertEquals(captured.submission!!.packs.map { it.identity },trace.diagnostics!!.context.identities)
            val source=trace.answer.sources.single();assertSame(source,capturedSource(trace.answer,id,"S1",id))
            passed("actual-recovery-cited-answer-has-new-owned-diagnostics-and-result-identity")
            val pack=captured.installed.single()
            instrument.runOnMainSync { model.inspectPack(pack.id,pack.version,pack.hash) };ready()
            assertSame(trace,model.state.value.trace);assertSame(captured.answer,model.state.value.answer)
            assertSame(captured.submission,model.state.value.submission);assertEquals(id,model.state.value.completedResultId)
            assertNotNull(model.state.value.details)
            instrument.runOnMainSync { model.closeDetails() };assertNull(model.state.value.detailRequest)
            assertSame(trace,model.state.value.trace)
            passed("fresh-read-only-inspection-and-close-preserve-reference-identical-completed-context")
            instrument.runOnMainSync { model.deactivate(pack.id) };ready()
            assertNull(model.state.value.trace);assertNull(model.state.value.answer);assertNull(model.state.value.submission)
            assertNull(model.state.value.completedResultId)
            assertNull(capturedSource(model.state.value.answer,model.state.value.completedResultId,"S1",id))
            assertEquals(question,trace.diagnostics!!.context.query.raw);assertEquals(source,trace.answer.sources.single())
            passed("pack-mutation-clears-live-result-but-independent-captured-diagnostics-remain-readable")
            instrument.runOnMainSync { model.ask(question,"2027-01-01") };ready()
            assertEquals("NO_ACTIVE_PACK",model.state.value.answer?.state)
            assertNotEquals(id,model.state.value.completedResultId);assertNotNull(model.state.value.completedResultId)
            assertNull(model.state.value.trace!!.diagnostics);assertEquals(0,model.state.value.trace!!.emittedTokens)
            assertNotNull(model.state.value.trace!!.session!!.generator)
            passed("new-no-active-outcome-distinguishes-loaded-session-from-current-generation")
            assertEquals(before,guard());passed("owner-default-registries-and-models-byte-identical-within-run")
            File(context.filesDir,"m4-diagnostic-lifecycle.json").writeText(JSONObject().put("status","PASS").put("cases",cases)
                .put("actual_native_replacement_entry",true).put("actual_native_cancel_entry",true).put("actual_recovery_generation",true)
                .put("recovery_answer",trace.answer.text).put("recovery_query",trace.diagnostics!!.context.query.raw)
                .put("recovery_manifest_sha256",source.pack.manifestSha256).put("canonical_sha256",source.canonicalTextSha256)
                .put("prefill_tokens",trace.prefillTokens).put("evidence_tokens",trace.evidenceTokens).put("emitted_tokens_including_terminal",trace.emittedTokens)
                .put("session_ask_wall_ms_excludes_queue_construction_ui",trace.totalMs).put("initialization_ms",trace.initializationMs)
                .put("owner_registry_and_model_sha256",JSONObject(before)).put("raw_reasoning_persisted",false)
                .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET")
                .put("limits","Isolated synthetic actual ViewModel controls; no final content, process-death, held-out accuracy, throughput, resource or thermal acceptance.").toString(2),Charsets.UTF_8)
        } finally {
            instrument.runOnMainSync { store.clear() };input.delete()
            val end=System.nanoTime()+10_000_000_000L;var released=false
            while(!released && System.nanoTime()<end) {
                released=runCatching { ProductSession(context,root,ProductConfiguration.keys(context),true).use { };true }.getOrDefault(false)
                if(!released) android.os.SystemClock.sleep(50)
            }
            check(released);require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));root.deleteRecursively()
        }
    }
}
