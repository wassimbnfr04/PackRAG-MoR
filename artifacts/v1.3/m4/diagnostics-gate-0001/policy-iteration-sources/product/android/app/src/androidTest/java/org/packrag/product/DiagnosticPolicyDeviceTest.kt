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
import org.packrag.runtime.RuntimeTrace

/** Actual compiled app policy and native ViewModel flow. Positive calibration is schema-only. */
@RunWith(AndroidJUnit4::class)
class DiagnosticPolicyDeviceTest {
    @Test fun approvedNativeDiagnosticsAndRejectedDeveloperImportKeepPolicyAndResultOwnership() {
        assertEquals("demo",BuildConfig.BUILD_TYPE);assertFalse(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext
        fun guard():Map<String,String> = listOf("packs","production-registry","models").flatMap { name ->
            val folder=File(context.filesDir,name);if(!folder.exists()) emptyList() else folder.walkTopDown().filter { it.isFile }
                .map { it.relativeTo(context.filesDir).path to Crypto.fileHash(it) }.toList()
        }.toMap()
        val before=guard();val root=File(context.filesDir,"diagnostic-policy-${UUID.randomUUID()}");val store=ViewModelStore()
        val input=File(context.cacheDir,"diagnostic-policy-${UUID.randomUUID()}.kpack");val cases=JSONArray()
        lateinit var model:PackRagViewModel;lateinit var cold:RuntimeTrace;lateinit var warm:RuntimeTrace
        val question="What is the maximum continuous operating temperature of the Aster-9?"
        val expectedManifest="da063519398922758871d9a42bb1fc8597a198c8da8eba27c1ef01806082c5af"
        fun passed(id:String) { cases.put(JSONObject().put("id",id).put("passed",true)) }
        fun ready() {
            val end=System.nanoTime()+600_000_000_000L
            while(model.state.value.busy && System.nanoTime()<end) android.os.SystemClock.sleep(20)
            assertFalse("Action timed out",model.state.value.busy)
        }
        fun ask(jurisdiction:String="") { instrument.runOnMainSync { model.ask(question,"2027-01-01",jurisdiction,true) };ready() }
        fun checked(trace:RuntimeTrace) {
            assertEquals("ANSWER_ACCEPTED",trace.answer.state);assertTrue(trace.answer.text!!.contains("74 °C"))
            assertTrue(trace.answer.text!!.contains("[S1]"));assertFalse(trace.answer.text!!.contains("</think>"))
            val source=trace.answer.sources.single();assertEquals(expectedManifest,source.pack.manifestSha256)
            assertEquals("266af80f5d4da1dac500acd9a2bcc1fd2317b2caf49141ebb586280b9df49333",source.canonicalTextSha256)
            assertEquals("ed25519:97e6f35dd5d63b1f8dfe88273283e283a24fec351f4a0f59ff3da3443d5ad950",source.metadata!!.publisherKeyId)
            val state=model.state.value;val data=requireNotNull(trace.diagnostics);val session=requireNotNull(trace.session)
            assertEquals(state.submission!!.query,data.context.query);assertEquals(question,data.context.query.raw)
            assertEquals(state.submission!!.packs.map { it.identity },data.context.identities)
            assertEquals(listOf(expectedManifest),data.context.identities.map { it.manifestSha256 })
            assertEquals(trace.evidenceContext!!.generator,data.context.generator)
            assertEquals(trace.evidenceContext!!.manifests,data.context.manifests)
            assertTrue(data.generationCalled);assertTrue(data.candidates!!.isNotEmpty())
            assertTrue(session.embedderInitialized);assertNotNull(session.generator)
            assertEquals("QAD-Q4_0 (configured hash-pinned artifact)",session.configured.quantization)
            for(value in listOf(data.embeddingMs,data.retrievalMs,data.admissionMs,session.generatorLoadAndVerificationMs))
                assertTrue(value!=null && value.isFinite() && value>=0)
            for(evidence in trace.evidence) {
                val row=data.candidates!!.single { it.key==evidence.originKey }
                assertEquals(evidence.packIdentity,row.identity);assertEquals(evidence.chunk.textSha256,row.canonicalSha256)
                assertEquals(evidence.exact,row.exact);assertEquals(evidence.sparseRank,row.sparseRank)
                assertEquals(evidence.denseRank,row.denseRank);assertEquals(evidence.cosine,row.cosine,0.0)
                assertEquals(evidence.rrf,row.rrf,0.0);assertEquals(evidence.relevant,row.relevant)
                assertEquals(evidence.finalRank,row.finalRank);assertEquals(evidence.originRecords,row.origins)
            }
            assertTrue(trace.prefillTokens<=1536 && trace.evidenceTokens<=1200 && trace.emittedTokens in 1..512)
            if(trace.reasoningTokens==null) assertNull(trace.finalAndTerminalTokens)
            else assertEquals(trace.emittedTokens,trace.reasoningTokens!!+trace.finalAndTerminalTokens!!)
        }
        try {
            instrument.runOnMainSync { model=PackRagViewModel(context.applicationContext as Application,root);store.put("test",model) };ready();ask()
            val empty=model.state.value;assertEquals("NO_ACTIVE_PACK",empty.answer?.state);assertNotNull(empty.completedResultId)
            assertNull(empty.trace!!.diagnostics);assertNull(empty.trace!!.session!!.generator)
            assertFalse(empty.trace!!.session!!.embedderInitialized);assertEquals(0.0,empty.trace!!.initializationMs,0.0)
            assertEquals(0,empty.trace!!.emittedTokens);passed("compiled-production-policy-fresh-no-pack-no-fabricated-load-or-generation")
            instrument.context.assets.open("release-trust-corpus/calibration-schema-only.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
            assertEquals("eb1d477f32e60ce97784320994d473690dd97ff4d13b49d921c93aad82b58011",Crypto.fileHash(input))
            instrument.runOnMainSync { model.importPack(Uri.fromFile(input)) };ready()
            assertNull(model.state.value.answer);assertEquals(1,model.state.value.packs.size)
            assertEquals(expectedManifest,model.state.value.installed.single().hash)
            passed("actual-viewmodel-approved-publisher-import-without-caller-trust-injection")
            ask();cold=requireNotNull(model.state.value.trace);checked(cold);val coldId=requireNotNull(model.state.value.completedResultId)
            ask();warm=requireNotNull(model.state.value.trace);checked(warm);val warmState=model.state.value
            val warmId=requireNotNull(warmState.completedResultId);assertNotEquals(coldId,warmId)
            assertTrue(cold.initializationMs>0);assertEquals(0.0,warm.initializationMs,0.0)
            assertEquals(cold.session!!.generatorLoadAndVerificationMs,warm.session!!.generatorLoadAndVerificationMs)
            assertEquals(cold.evidence.map { it.originKey },warm.evidence.map { it.originKey })
            passed("actual-approved-cold-warm-native-citations-owned-candidates-pins-and-token-partitions")
            val pack=warmState.installed.single()
            instrument.runOnMainSync { model.inspectPack(pack.id,pack.version,pack.hash) };ready()
            assertSame(warm,model.state.value.trace);assertSame(warmState.answer,model.state.value.answer)
            assertSame(warmState.submission,model.state.value.submission);assertEquals(warmId,model.state.value.completedResultId)
            assertEquals(expectedManifest,model.state.value.details!!.identity.manifestSha256)
            instrument.runOnMainSync { model.closeDetails() }
            passed("read-only-production-inspection-retains-reference-identical-completed-result")
            ask("MA");val excluded=model.state.value;assertEquals("NO_RELEVANT_EVIDENCE",excluded.answer?.state)
            assertNotEquals(warmId,excluded.completedResultId);assertEquals("MA",excluded.trace!!.diagnostics!!.context.query.jurisdiction)
            assertTrue(excluded.trace!!.diagnostics!!.candidates!!.isEmpty());assertFalse(excluded.trace!!.diagnostics!!.generationCalled)
            assertEquals(0,excluded.trace!!.emittedTokens);assertNull(excluded.answer!!.text)
            assertNull(capturedSource(excluded.answer,excluded.completedResultId,"S1",warmId))
            passed("new-jurisdiction-abstention-records-no-generation-and-cannot-reuse-prior-result")
            instrument.runOnMainSync { model.deactivate(pack.id) };ready()
            assertNull(model.state.value.trace);assertNull(model.state.value.submission);assertNull(model.state.value.completedResultId)
            ask();assertEquals("NO_ACTIVE_PACK",model.state.value.answer?.state)
            assertNotNull(model.state.value.trace!!.session!!.generator);assertNull(model.state.value.trace!!.diagnostics)
            assertEquals(0,model.state.value.trace!!.emittedTokens)
            passed("production-mutation-clears-attribution-and-no-active-distinguishes-previously-loaded-session")
            val payloads=File(root,"packs").let { folder -> if(!folder.exists()) emptyMap() else folder.walkTopDown().filter { it.isFile }
                .associate { it.relativeTo(folder).path to Crypto.fileHash(it) } }
            instrument.context.assets.open("walking-skeleton.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
            assertEquals("19da286b9f0860c312dc8d14ce0ee8681bf12ca092a7b8a12171fd86abe02c7f",Crypto.fileHash(input))
            instrument.runOnMainSync { model.importPack(Uri.fromFile(input)) };ready()
            assertEquals("RUNTIME_ERROR",model.state.value.answer?.state);assertNull(model.state.value.trace)
            assertNull(model.state.value.submission);assertNull(model.state.value.completedResultId);assertTrue(model.state.value.packs.isEmpty())
            assertEquals(expectedManifest,model.state.value.installed.single().hash)
            assertEquals(payloads,File(root,"packs").let { folder -> if(!folder.exists()) emptyMap() else folder.walkTopDown().filter { it.isFile }
                .associate { it.relativeTo(folder).path to Crypto.fileHash(it) } })
            assertEquals(question,cold.diagnostics!!.context.query.raw);assertEquals(expectedManifest,warm.answer.sources.single().pack.manifestSha256)
            passed("actual-production-developer-import-rejected-clears-live-result-retains-approved-inactive-payload")
            assertEquals(before,guard());passed("owner-default-registries-models-and-signed-payloads-byte-identical")
            fun recorded(trace:RuntimeTrace)=JSONObject().put("outcome",trace.answer.state).put("answer",trace.answer.text)
                .put("manifest_sha256",trace.answer.sources.single().pack.manifestSha256)
                .put("canonical_sha256",trace.answer.sources.single().canonicalTextSha256)
                .put("initialization_ms",trace.initializationMs).put("session_ask_wall_ms_excludes_queue_construction_ui",trace.totalMs)
                .put("prefill_tokens",trace.prefillTokens).put("evidence_tokens",trace.evidenceTokens)
                .put("emitted_tokens_including_terminal",trace.emittedTokens).put("reasoning_through_closing_marker",trace.reasoningTokens ?: JSONObject.NULL)
                .put("remaining_final_and_terminal",trace.finalAndTerminalTokens ?: JSONObject.NULL)
                .put("candidate_count",trace.diagnostics!!.candidates!!.size).put("configured_quantization",trace.session!!.configured.quantization)
            File(context.filesDir,"m4-diagnostic-policy.json").writeText(JSONObject().put("status","PASS").put("cases",cases)
                .put("compiled_developer_mode",false).put("build_type",BuildConfig.BUILD_TYPE).put("actual_weight_inference",true)
                .put("cold",recorded(cold)).put("warm",recorded(warm)).put("owner_registry_and_model_sha256",JSONObject(before))
                .put("raw_reasoning_persisted",false).put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET")
                .put("limits","Compiled demo policy in instrumentable debug-signed APK; not final release. Approved synthetic schema-only calibration fixture is not genuine measured calibration, final content, held-out accuracy or performance acceptance.").toString(2),Charsets.UTF_8)
        } finally {
            instrument.runOnMainSync { store.clear() };input.delete();val end=System.nanoTime()+10_000_000_000L;var released=false
            while(!released && System.nanoTime()<end) {
                released=runCatching { ProductSession(context,root,ProductConfiguration.keys(context),false).use { };true }.getOrDefault(false)
                if(!released) android.os.SystemClock.sleep(50)
            }
            check(released);require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));root.deleteRecursively()
        }
    }
}
