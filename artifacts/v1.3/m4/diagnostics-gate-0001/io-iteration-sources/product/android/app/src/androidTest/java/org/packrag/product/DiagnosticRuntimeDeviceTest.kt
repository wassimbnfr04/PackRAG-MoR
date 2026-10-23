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
import org.packrag.runtime.RuntimeTrace
import org.packrag.runtime.candidateDiagnostic
import org.packrag.retrieval.Candidate
import org.packrag.model.RepresentationFailure
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.asContextElement
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext

/** Actual pinned LFM/Granite and session, isolated development fixture. */
@RunWith(AndroidJUnit4::class)
class DiagnosticRuntimeDeviceTest {
    @Test fun actualColdWarmAndNoPackDiagnosticsKeepOwnedContextAfterReaderClose() {
        assertTrue(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext
        fun guard():Map<String,String> = listOf("packs","production-registry","models").flatMap { name ->
            val folder=File(context.filesDir,name);if(!folder.exists()) emptyList() else folder.walkTopDown().filter { it.isFile }
                .map { it.relativeTo(context.filesDir).path to Crypto.fileHash(it) }.toList()
        }.toMap()
        val before=guard();val root=File(context.filesDir,"diagnostic-runtime-${UUID.randomUUID()}");assertTrue(root.mkdirs())
        val input=File(root,"walking.kpack");val cases=JSONArray();lateinit var cold:RuntimeTrace;lateinit var warm:RuntimeTrace
        val cpuMarker=ThreadLocal<String>();val observations=java.util.Collections.synchronizedList(mutableListOf<Pair<String,String?>>())
        fun askOnCpu(session:ProductSession,query:Query):RuntimeTrace=runBlocking {
            withContext(Dispatchers.Default+cpuMarker.asContextElement("CPU_DEFAULT")) { session.ask(query) }
        }
        fun passed(name:String) { cases.put(JSONObject().put("id",name).put("passed",true)) }
        val query=Query("What is the maximum continuous operating temperature of the Aster-9?","2027-01-01",null,true)
        try {
            instrument.context.assets.open("walking-skeleton.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
            assertEquals("19da286b9f0860c312dc8d14ce0ee8681bf12ca092a7b8a12171fd86abe02c7f",Crypto.fileHash(input))
            ProductSession(context,File(root,"registry"),ProductConfiguration.keys(context),true) { label ->
                observations.add(label to cpuMarker.get())
            }.use { session ->
                val empty=askOnCpu(session,query)
                assertEquals("NO_ACTIVE_PACK",empty.answer.state);assertNull(empty.diagnostics)
                assertNull(empty.session!!.generator);assertFalse(empty.session!!.embedderInitialized)
                assertNull(session.generatorLoadAndVerificationMs);assertEquals(0,empty.emittedTokens)
                passed("fresh-no-active-pack-has-no-native-initialization-or-fabricated-pool")
                val pack=session.registry.activate(input)
                // Fixed constructor control: deliberately missing rendering, not a new signed foreign pack.
                val foreign=pack.chunks.first().copy(language="fr",id="diagnostic-missing-rendering-control")
                val control=Candidate(pack,foreign,false,2,5,.375,.03125,true,finalRank=7)
                assertThrows(RepresentationFailure::class.java) { control.generatorRendering }
                val copied=candidateDiagnostic(control)
                assertEquals(control.originKey,copied.key);assertEquals(control.packIdentity,copied.identity)
                assertEquals(foreign.id,copied.chunkId);assertEquals(foreign.sourceId,copied.sourceId)
                assertEquals(foreign.textSha256,copied.canonicalSha256);assertEquals(foreign.originalSha256,copied.originalSha256)
                assertFalse(copied.exact);assertEquals(2,copied.sparseRank);assertEquals(5,copied.denseRank)
                assertEquals(.375,copied.cosine,0.0);assertEquals(.03125,copied.rrf,0.0)
                assertTrue(copied.relevant);assertEquals(7,copied.finalRank)
                passed("fixed-unequal-metadata-conversion-does-not-request-missing-rendering")
                cold=askOnCpu(session,query);warm=askOnCpu(session,query)
                assertEquals(listOf("ENCODER_CONSTRUCTOR","GENERATOR_CONSTRUCTOR","RUNTIME_CPU","SQLITE_SPARSE","RUNTIME_CPU","SQLITE_SPARSE"),observations.map { it.first })
                assertTrue(observations.all { (label,marker) -> if(label=="RUNTIME_CPU") marker=="CPU_DEFAULT" else marker==null })
                val executorField=BlockingIo::class.java.getDeclaredField("executor");executorField.isAccessible=true
                val executor=requireNotNull(executorField.get(BlockingIo))
                assertSame(Dispatchers.IO,executor)
                passed("real-cold-warm-runtime-on-marked-default-and-fixed-io-dispatcher-without-monitor-suspension")
                for(trace in listOf(cold,warm)) {
                    assertEquals("ANSWER_ACCEPTED",trace.answer.state);assertTrue(trace.answer.text!!.contains("74 °C"))
                    assertTrue(trace.answer.sources.isNotEmpty());assertFalse(trace.answer.text!!.contains("</think>"))
                    val data=requireNotNull(trace.diagnostics);assertTrue(data.generationCalled);assertEquals(query,data.context.query)
                    assertTrue(data.candidates!!.isNotEmpty());assertEquals(data.context.identities,trace.evidenceContext!!.identities)
                    assertEquals(data.context.manifests,trace.evidenceContext!!.manifests)
                    assertEquals(data.context.generator,trace.evidenceContext!!.generator)
                    assertTrue(trace.session!!.embedderInitialized);assertNotNull(trace.session!!.generator)
                    assertEquals("QAD-Q4_0 (configured hash-pinned artifact)",trace.session!!.configured.quantization)
                    for(value in listOf(data.embeddingMs,data.retrievalMs,data.admissionMs,trace.session!!.generatorLoadAndVerificationMs))
                        assertTrue(value!=null && value.isFinite() && value>=0)
                    assertTrue(trace.evidence.all { evidence -> data.candidates!!.any { row -> row.key==evidence.originKey
                        && row.identity==evidence.packIdentity && row.canonicalSha256==evidence.chunk.textSha256 } })
                    for(evidence in trace.evidence) {
                        val row=data.candidates!!.single { it.key==evidence.originKey }
                        assertEquals(evidence.exact,row.exact);assertEquals(evidence.sparseRank,row.sparseRank)
                        assertEquals(evidence.denseRank,row.denseRank);assertEquals(evidence.cosine,row.cosine,0.0)
                        assertEquals(evidence.rrf,row.rrf,0.0);assertEquals(evidence.relevant,row.relevant)
                        assertEquals(evidence.finalRank,row.finalRank);assertEquals(evidence.originRecords,row.origins)
                    }
                    assertTrue(data.candidates!!.all { it.origins.isNotEmpty() && it.cosine.isFinite() && it.rrf.isFinite() })
                    if(trace.reasoningTokens==null) assertNull(trace.finalAndTerminalTokens)
                    else assertEquals(trace.emittedTokens,trace.reasoningTokens!!+trace.finalAndTerminalTokens!!)
                    assertTrue(trace.prefillTokens<=1536 && trace.evidenceTokens<=1200 && trace.emittedTokens in 1..512)
                }
                assertTrue(cold.initializationMs>0);assertEquals(0.0,warm.initializationMs,0.0)
                assertEquals(cold.session!!.generatorLoadAndVerificationMs,warm.session!!.generatorLoadAndVerificationMs)
                passed("actual-cold-and-warm-cited-generation-have-captured-candidates-identities-and-scoped-timings")
                val diagnostic=requireNotNull(cold.diagnostics);val manifest=diagnostic.context.manifests.single()
                val keys=diagnostic.candidates!!.map { it.key };val identities=diagnostic.context.identities.toList()
                val details=session.registry.inspect(pack.id,pack.version,pack.manifestHash)
                assertEquals(identities.single(),details.identity);assertEquals(manifest,diagnostic.context.manifests.single())
                passed("read-only-inspection-retains-original-diagnostics")
                pack.manifest.getJSONObject("publisher").put("name","test-only-live-mutation-after-completed-queries")
                assertEquals(manifest,diagnostic.context.manifests.single());assertEquals(keys,diagnostic.candidates!!.map { it.key })
                session.registry.deactivate(pack.id)
                val noPack=askOnCpu(session,query)
                assertEquals("NO_ACTIVE_PACK",noPack.answer.state);assertNull(noPack.diagnostics)
                assertNotNull(noPack.session!!.generator);assertTrue(noPack.session!!.embedderInitialized)
                assertEquals(0,noPack.emittedTokens);assertEquals(0.0,noPack.initializationMs,0.0)
                passed("no-active-after-deactivation-distinguishes-previously-loaded-model-from-current-generation")
            }
            assertEquals(query,cold.diagnostics!!.context.query);assertTrue(cold.diagnostics!!.candidates!!.isNotEmpty())
            assertThrows(UnsupportedOperationException::class.java) { (cold.diagnostics!!.candidates as MutableList).clear() }
            passed("captured-diagnostics-outlive-session-readers-and-reject-list-mutation")
            assertEquals(before,guard());passed("owner-models-and-default-registries-unchanged")
            fun recorded(trace:RuntimeTrace):JSONObject {
                val data=requireNotNull(trace.diagnostics)
                return JSONObject().put("outcome",trace.answer.state).put("answer",trace.answer.text)
                    .put("query",data.context.query.raw).put("as_of",data.context.query.asOf)
                    .put("initialization_ms",trace.initializationMs).put("session_ask_wall_ms",trace.totalMs)
                    .put("embedding_ms",data.embeddingMs).put("retrieval_ms",data.retrievalMs).put("admission_ms",data.admissionMs)
                    .put("prefill_tokens",trace.prefillTokens).put("evidence_tokens",trace.evidenceTokens).put("emitted_tokens_including_terminal",trace.emittedTokens)
                    .put("reasoning_through_closing_marker",trace.reasoningTokens ?: JSONObject.NULL)
                    .put("remaining_final_and_terminal",trace.finalAndTerminalTokens ?: JSONObject.NULL)
                    .put("generator_constructor_load_and_verification_ms",trace.session!!.generatorLoadAndVerificationMs)
                    .put("candidate_rows",JSONArray(data.candidates!!.map { row -> JSONObject().put("key",row.key)
                        .put("pack_id",row.identity.packId).put("version",row.identity.version).put("manifest_sha256",row.identity.manifestSha256)
                        .put("chunk_id",row.chunkId).put("source_id",row.sourceId).put("canonical_sha256",row.canonicalSha256)
                        .put("sparse_rank",row.sparseRank ?: JSONObject.NULL).put("dense_rank",row.denseRank ?: JSONObject.NULL)
                        .put("cosine",row.cosine).put("rrf",row.rrf).put("relevant",row.relevant).put("exact",row.exact)
                        .put("selection",candidateSelection(trace,row.key)).put("origin_count",row.origins.size) }))
            }
            File(context.filesDir,"m4-diagnostic-runtime.json").writeText(JSONObject().put("status","PASS").put("cases",cases)
                .put("cold",recorded(cold)).put("warm",recorded(warm)).put("actual_weight_inference",true)
                .put("execution_boundary_observations",JSONArray(observations.map { (label,marker) ->
                    JSONObject().put("operation",label).put("caller_default_context_marker",marker ?: JSONObject.NULL) }))
                .put("owner_registry_and_model_sha256",JSONObject(before)).put("raw_reasoning_persisted",false)
                .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET")
                .put("limits","Synthetic functional scope; no held-out quality, peak-memory, throughput, thermal, radio-isolation or causal bottleneck acceptance.").toString(2),Charsets.UTF_8)
        } finally {
            require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));root.deleteRecursively()
        }
    }
}
