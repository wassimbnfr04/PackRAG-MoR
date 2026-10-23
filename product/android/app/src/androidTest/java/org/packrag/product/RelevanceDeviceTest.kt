package org.packrag.product

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID
import kotlin.math.abs
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.embedding.GraniteEncoder
import org.packrag.generator.LlamaGenerator
import org.packrag.model.Query
import org.packrag.model.RelevanceGate
import org.packrag.model.RelevanceSignal
import org.packrag.packs.ActivePack
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier
import org.packrag.retrieval.Retrieval
import org.packrag.runtime.Prompt

/** Synthetic fixed thresholds test wiring; they are not measured release calibration. */
@RunWith(AndroidJUnit4::class)
class RelevanceDeviceTest {
    @Test fun fixedGateSignedGlobalRetrievalAndActualTokenizer() {
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext;val assets=instrument.context.assets
        val reference=assets.open("relevance-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val fixedBytes=assets.open("relevance-corpus/relevance-contracts.json").use { it.readBytes() }
        assertEquals(reference.getString("fixed_gate_sha256"),Crypto.sha256(fixedBytes))
        val fixed=JSONObject(fixedBytes.toString(Charsets.UTF_8)).getJSONArray("cases");assertEquals(32,fixed.length())
        for(i in 0 until fixed.length()) {
            val case=fixed.getJSONObject(i);val rows=case.getJSONArray("signals")
            val signals=(0 until rows.length()).map { j -> val row=rows.getJSONObject(j)
                RelevanceSignal(row.getBoolean("exact"),if(row.isNull("sparse_rank")) null else row.getInt("sparse_rank"),
                    if(row.isNull("dense_rank")) null else row.getInt("dense_rank"),row.getDouble("dense_score"),row.getBoolean("calibrated"),
                    if(row.isNull("agreed_threshold")) null else row.getDouble("agreed_threshold"),
                    if(row.isNull("dense_only_threshold")) null else row.getDouble("dense_only_threshold")) }
            val flags=case.getJSONArray("expected")
            assertEquals(case.getString("id"),(0 until flags.length()).map { flags.getBoolean(it) },RelevanceGate.mark(signals))
        }
        val public=assets.open("relevance-corpus/public-key.raw").use { it.readBytes() };assertEquals(reference.getString("public_key_sha256"),Crypto.sha256(public))
        val lock=context.assets.open("toolchain.lock.json").bufferedReader().use { JSONObject(it.readText()) }.getJSONObject("embedder")
        val schema=context.assets.open("schema.sql").bufferedReader().use { it.readText() }
        val root=File(context.filesDir,"relevance-parity-${UUID.randomUUID()}");assertTrue(root.mkdirs());val results=JSONArray()
        try {
            PackRegistry(File(root,"registry"),PackVerifier(listOf(public),lock.getJSONObject("pack_profile"),schema,true)).use { registry ->
                val packs=linkedMapOf<String,ActivePack>();val records=reference.getJSONArray("packs")
                for(i in 0 until records.length()) {
                    val row=records.getJSONObject(i);val archive=File(root,row.getString("filename"))
                    assets.open("relevance-corpus/"+archive.name).use { source -> archive.outputStream().use { source.copyTo(it) } }
                    assertEquals(row.getString("sha256"),Crypto.fileHash(archive));packs[row.getString("id")]=registry.activate(archive)
                }
                val hashes=lock.getJSONObject("asset_sha256");val models=File(context.filesDir,"models")
                GraniteEncoder(File(models,"granite"),hashes.getString("tokenizer.json"),hashes.getString("onnx/model.onnx")).use { encoder ->
                    LlamaGenerator(File(models,"LFM2.5-2.6B-QAD-Q4_0.gguf"),File(models,"chat_template.jinja"),vocabularyOnly=true).use { tokenizer ->
                        val vectors=mutableMapOf<String,FloatArray>();val cases=reference.getJSONArray("cases");assertEquals(8,cases.length())
                        for(i in 0 until cases.length()) {
                            val case=cases.getJSONObject(i);val label=case.getString("id");val query=Query(case.getString("raw"),case.getString("as_of"))
                            val vector=vectors.getOrPut(query.normalized) { encoder.encode(query.normalized) };val stored=case.getJSONArray("query_vector")
                            var maxEmbedding=0.0;for(j in vector.indices)maxEmbedding=maxOf(maxEmbedding,abs(vector[j]-stored.getDouble(j)))
                            assertTrue(label+": embedding",maxEmbedding<=1e-4)
                            val active=relevanceStrings(case.getJSONArray("packs")).map { packs.getValue(it) };val actual=Retrieval.retrieve(active,query,vector)
                            assertFalse(actual.ambiguous);assertEquals(actual,Retrieval.retrieve(active.reversed(),query,vector))
                            assertEquals(label,relevanceStrings(case.getJSONArray("expected_order")),actual.candidates.map { it.pack.id.removePrefix("org.packrag.contract.") })
                            val expected=case.getJSONArray("candidates");assertEquals(label,expected.length(),actual.candidates.size);var maxCosine=0.0
                            for((rank,candidate) in actual.candidates.withIndex()) {
                                val row=expected.getJSONObject(rank)
                                assertEquals(row.getString("pack_id"),candidate.pack.id);assertEquals(row.getString("chunk_id"),candidate.chunk.id)
                                assertEquals(row.getBoolean("exact"),candidate.exact);assertEquals(row.getBoolean("relevant"),candidate.relevant)
                                assertEquals(if(row.isNull("sparse_rank")) null else row.getInt("sparse_rank"),candidate.sparseRank)
                                assertEquals(if(row.isNull("dense_rank")) null else row.getInt("dense_rank"),candidate.denseRank)
                                assertEquals(row.getDouble("rrf"),candidate.rrf,1e-12);maxCosine=maxOf(maxCosine,abs(row.getDouble("cosine")-candidate.cosine))
                                val origins=row.getJSONArray("origins")
                                assertEquals((0 until origins.length()).map { j -> val o=origins.getJSONArray(j);"${o.getString(0)}@${o.getString(1)}:${o.getString(2)}" },candidate.origins)
                            }
                            assertTrue(label+": cosine",maxCosine<=1e-4)
                            val tokens=JSONObject();val relevant=actual.candidates.any { it.relevant }
                            if(relevant) {
                                val prepared=Prompt.prepare(query,active,actual.candidates,tokenizer)
                                assertTrue(prepared.tokens.size<=1536 && prepared.evidenceTokens<=1200 && prepared.evidence.size<=4 && prepared.maximum<=512)
                                tokens.put("tokens",JSONArray(prepared.tokens.toList())).put("prefill_tokens",prepared.tokens.size)
                                    .put("evidence_tokens",prepared.evidenceTokens).put("max_new",prepared.maximum).put("selected",JSONArray(prepared.evidence.map { it.chunk.id }))
                            }
                            results.put(JSONObject().put("id",label).put("status","PASS").put("candidate_count",actual.candidates.size)
                                .put("max_embedding_abs_error",maxEmbedding).put("max_dense_cosine_error",maxCosine)
                                .put("admission",if(relevant) "READY" else "NO_RELEVANT_EVIDENCE").put("actual_tokenizer",tokens))
                        }
                    }
                }
            }
            File(context.filesDir,"m4-relevance.json").writeText(JSONObject().put("status","PASS").put("fixed_contract_cases",32).put("signed_packs",8)
                .put("retrieval_cases",results).put("purpose","SIGNED_SYNTHETIC_GLOBAL_GATE_NOT_MEASURED_CALIBRATION")
                .put("developer_trust","EXPLICIT_ISOLATED_TEST_KEYS_NOT_PRODUCTION_DEFAULT").toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));root.deleteRecursively() }
    }

    @Test fun actualRuntimeStopsAtMergedGateOrAnswersWithCitations() {
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext;val assets=instrument.context.assets
        val reference=assets.open("relevance-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val public=assets.open("relevance-corpus/public-key.raw").use { it.readBytes() };assertEquals(reference.getString("public_key_sha256"),Crypto.sha256(public))
        val root=File(context.filesDir,"relevance-runtime-${UUID.randomUUID()}");assertTrue(root.mkdirs());val results=JSONArray()
        try {
            ProductSession(context,File(root,"registry"),listOf(public),true).use { session ->
                val packs=linkedMapOf<String,ActivePack>();val records=reference.getJSONArray("packs")
                for(i in 0 until records.length()) {
                    val row=records.getJSONObject(i);val archive=File(root,row.getString("filename"))
                    assets.open("relevance-corpus/"+archive.name).use { source -> archive.outputStream().use { source.copyTo(it) } }
                    assertEquals(row.getString("sha256"),Crypto.fileHash(archive));packs[row.getString("id")]=session.registry.activate(archive)
                }
                val cases=reference.getJSONArray("cases")
                for(label in listOf("TOP_FAIL_LOWER_PASS","TOP_UNCAL_LOWER_PASS","TOP_PASS_LOWER_PASS","LEGACY_STATUS_DEFAULT")) {
                    session.registry.snapshot().toList().forEach { session.registry.deactivate(it.id) }
                    val case=(0 until cases.length()).map { cases.getJSONObject(it) }.single { it.getString("id")==label }
                    for(name in relevanceStrings(case.getJSONArray("packs"))) { val pack=packs.getValue(name);session.registry.activateInstalled(pack.id,pack.version) }
                    val trace=session.ask(Query(case.getString("raw"),case.getString("as_of")));val guarded=case.getString("expected_state")=="NO_RELEVANT_EVIDENCE"
                    val observed=JSONObject().put("id",label).put("status","OBSERVED_NOT_ACCEPTANCE").put("state",trace.answer.state)
                        .put("answer",trace.answer.text ?: JSONObject.NULL).put("selected",JSONArray(trace.selected))
                        .put("prefill_tokens",trace.prefillTokens).put("evidence_tokens",trace.evidenceTokens).put("emitted_tokens_including_terminal",trace.emittedTokens)
                        .put("total_ms_including_lazy_initialization",trace.totalMs).put("initialization_ms",trace.initializationMs)
                        .put("actual_weight_inference",!guarded).put("model_load_not_excluded",true)
                    File(context.filesDir,"m4-relevance-runtime-observed.json").writeText(observed.toString(2),Charsets.UTF_8)
                    assertEquals(label,case.getString("expected_state"),trace.answer.state)
                    if(guarded) { assertNull(trace.answer.text);assertEquals(0,trace.emittedTokens);assertEquals(0,trace.prefillTokens);assertTrue(trace.selected.isEmpty()) }
                    else {
                        assertTrue(label,trace.answer.text!!.contains("74 °C"));assertFalse(trace.answer.text!!.contains("</think>"));assertTrue(trace.answer.sources.isNotEmpty())
                        assertTrue(trace.answer.sources.all { it.canonicalText.contains("74 °C") })
                        assertTrue(trace.prefillTokens<=1536 && trace.evidenceTokens<=1200 && trace.emittedTokens in 1..512)
                    }
                    observed.put("status","PASS");results.put(observed)
                    File(context.filesDir,"m4-relevance-runtime-progress.json").writeText(JSONObject().put("status","RUNNING").put("cases",results).toString(2),Charsets.UTF_8)
                }
            }
            File(context.filesDir,"m4-relevance-runtime.json").writeText(JSONObject().put("status","PASS").put("cases",results).put("raw_reasoning_persisted",false)
                .put("purpose","ACTUAL_LFM_SYNTHETIC_GATE_NOT_RELEASE_CALIBRATION_GOLD_OR_PERFORMANCE").put("developer_trust","EXPLICIT_ISOLATED_TEST_KEYS_NOT_PRODUCTION_DEFAULT")
                .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET").toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));root.deleteRecursively() }
    }
}

private fun relevanceStrings(rows:JSONArray):List<String> = (0 until rows.length()).map { rows.getString(it) }
