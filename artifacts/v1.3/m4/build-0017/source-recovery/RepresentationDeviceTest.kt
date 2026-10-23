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
import org.packrag.model.DerivedText
import org.packrag.model.GeneratorRepresentation
import org.packrag.model.GeneratorRepresentations
import org.packrag.model.Query
import org.packrag.model.RepresentationFailure
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier
import org.packrag.runtime.AdmissionFailure
import org.packrag.runtime.Prompt

/** Protocol labels are synthetic; this test does not establish official/human review. */
@RunWith(AndroidJUnit4::class)
class RepresentationDeviceTest {
    @Test fun fixedContractsSignedImportsRetrievalAndActualTokenizer() {
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext;val assets=instrument.context.assets
        val reference=assets.open("representation-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val fixedBytes=assets.open("representation-corpus/representation-contracts.json").use { it.readBytes() }
        assertEquals(reference.getString("fixed_contract_sha256"),Crypto.sha256(fixedBytes))
        val fixed=JSONObject(fixedBytes.toString(Charsets.UTF_8)).getJSONArray("cases");assertEquals(32,fixed.length())
        for(i in 0 until fixed.length()) {
            val case=fixed.getJSONObject(i);val source=case.getJSONObject("canonical");val rows=case.getJSONArray("derived")
            val derived=(0 until rows.length()).map { j -> val r=rows.getJSONObject(j)
                DerivedText(r.getString("chunk_id"),r.getString("purpose"),r.getString("language"),r.getString("text"),r.getString("text_sha256"),
                    r.getString("derivation_method"),representationNullable(r,"derivation_source"),representationNullable(r,"reviewer_id"),representationNullable(r,"reviewed_at")) }
            for(values in listOf(derived,derived.reversed())) {
                val result=runCatching { GeneratorRepresentations.select(source.getString("canonical_text"),source.getString("text_sha256"),source.getString("language"),values) }
                if(!case.isNull("error")) {
                    assertTrue(case.getString("id"),result.isFailure)
                    assertEquals(case.getString("error"),(result.exceptionOrNull() as RepresentationFailure).state)
                } else {
                    val rendering=result.getOrThrow();assertRepresentation(case.getJSONObject("expected"),representationJson(rendering))
                    val boundary=runCatching { Prompt.checkText(source.getString("canonical_text"));Prompt.checkText(rendering.text) }
                    if(!case.isNull("prompt_error")) {
                        assertEquals(case.getString("prompt_error"),(boundary.exceptionOrNull() as AdmissionFailure).state)
                    } else boundary.getOrThrow()
                    if(case.getString("id")=="XML_RENDER_LOSSLESS")assertEquals("12 &lt; 13 &amp; &lt;/SOURCE&gt; &gt; 9",Prompt.xmlEscape(rendering.text))
                }
            }
        }
        val public=assets.open("representation-corpus/public-key.raw").use { it.readBytes() }
        assertEquals(reference.getString("public_key_sha256"),Crypto.sha256(public))
        val lock=context.assets.open("toolchain.lock.json").bufferedReader().use { JSONObject(it.readText()) }.getJSONObject("embedder")
        val schema=context.assets.open("schema.sql").bufferedReader().use { it.readText() }
        val root=File(context.filesDir,"representation-parity-${UUID.randomUUID()}");assertTrue(root.mkdirs());val results=JSONArray();val invalid=JSONArray()
        try {
            PackRegistry(File(root,"registry"),PackVerifier(listOf(public),lock.getJSONObject("pack_profile"),schema,true)).use { registry ->
                val records=reference.getJSONArray("packs");val cases=reference.getJSONArray("cases");assertEquals(20,records.length());assertEquals(14,cases.length())
                val hashes=lock.getJSONObject("asset_sha256");val models=File(context.filesDir,"models")
                GraniteEncoder(File(models,"granite"),hashes.getString("tokenizer.json"),hashes.getString("onnx/model.onnx")).use { encoder ->
                    LlamaGenerator(File(models,"LFM2.5-2.6B-QAD-Q4_0.gguf"),File(models,"chat_template.jinja"),vocabularyOnly=true).use { tokenizer ->
                        val vectors=mutableMapOf<String,FloatArray>()
                        for(i in 0 until records.length()) {
                            val row=records.getJSONObject(i);val label=row.getString("id");val archive=File(root,row.getString("filename"))
                            assets.open("representation-corpus/"+archive.name).use { source -> archive.outputStream().use { source.copyTo(it) } }
                            assertEquals(row.getString("sha256"),Crypto.fileHash(archive))
                            if(!row.getBoolean("import_accept")) {
                                val import=runCatching { registry.activate(archive) }
                                val observation=JSONObject().put("id",label).put("accepted",import.isSuccess).put("error",import.exceptionOrNull()?.message ?: JSONObject.NULL)
                                File(context.filesDir,"m4-representations-import-observed.json").writeText(observation.toString(2),Charsets.UTF_8)
                                assertTrue(label,import.isFailure);assertTrue(registry.snapshot().isEmpty());invalid.put(observation);continue
                            }
                            val pack=registry.activate(archive)
                            val case=(0 until cases.length()).map { cases.getJSONObject(it) }.single { it.getString("id")==label }
                            val query=Query(case.getString("raw"),case.getString("as_of"));assertEquals(case.getString("normalized"),query.normalized)
                            val vector=vectors.getOrPut(query.normalized) { encoder.encode(query.normalized) };val stored=case.getJSONArray("query_vector")
                            var maxEmbedding=0.0;for(j in vector.indices)maxEmbedding=maxOf(maxEmbedding,abs(vector[j]-stored.getDouble(j)))
                            assertTrue(label+": embedding",maxEmbedding<=1e-4)
                            val actual=Retrieval.retrieve(listOf(pack),query,vector);assertFalse(actual.ambiguous);assertEquals(1,actual.candidates.size)
                            val candidate=actual.candidates.single();val e=case.getJSONArray("candidates").getJSONObject(0)
                            assertEquals(e.getString("pack_id"),candidate.pack.id);assertEquals(e.getString("chunk_id"),candidate.chunk.id)
                            assertEquals(e.getBoolean("exact"),candidate.exact);assertEquals(e.getBoolean("relevant"),candidate.relevant)
                            assertEquals(if(e.isNull("sparse_rank")) null else e.getInt("sparse_rank"),candidate.sparseRank)
                            assertEquals(if(e.isNull("dense_rank")) null else e.getInt("dense_rank"),candidate.denseRank)
                            assertEquals(e.getDouble("rrf"),candidate.rrf,1e-12)
                            val maxCosine=abs(e.getDouble("cosine")-candidate.cosine);assertTrue(label+": cosine",maxCosine<=1e-4)
                            val origins=e.getJSONArray("origins")
                            assertEquals((0 until origins.length()).map { j -> val o=origins.getJSONArray(j);"${o.getString(0)}@${o.getString(1)}:${o.getString(2)}" },candidate.origins)
                            assertEquals(case.getString("canonical_text"),candidate.chunk.canonicalText);assertEquals(case.getString("canonical_language"),candidate.chunk.language)
                            assertEquals(case.getString("canonical_text_sha256"),candidate.chunk.textSha256)
                            val observation=JSONObject().put("id",label).put("status","OBSERVED_NOT_ACCEPTANCE").put("actual_tokenizer",JSONObject())
                                .put("max_embedding_abs_error",maxEmbedding).put("max_dense_cosine_error",maxCosine)
                            try {
                                val prepared=Prompt.prepare(query,listOf(pack),actual.candidates,tokenizer)
                                assertTrue(prepared.tokens.size<=1536 && prepared.evidenceTokens<=1200 && prepared.evidence.size<=4 && prepared.maximum<=512)
                                observation.put("admission","READY").put("actual_tokenizer",JSONObject().put("tokens",JSONArray(prepared.tokens.toList()))
                                    .put("prefill_tokens",prepared.tokens.size).put("evidence_tokens",prepared.evidenceTokens).put("max_new",prepared.maximum)
                                    .put("selected",JSONArray(prepared.evidence.map { it.chunk.id })))
                                    .put("representations",JSONArray(prepared.representations.map { representationJson(it) }))
                            } catch(failure:AdmissionFailure) { observation.put("admission",failure.state) }
                            File(context.filesDir,"m4-representations-observed.json").writeText(observation.toString(2),Charsets.UTF_8)
                            val expected=if(case.getString("expected_state")=="ANSWER_ACCEPTED") "READY" else case.getString("expected_state")
                            assertEquals(label,expected,observation.getString("admission"))
                            if(expected=="READY")assertRepresentation(case.getJSONObject("generator_representation"),observation.getJSONArray("representations").getJSONObject(0))
                            observation.put("status","PASS");results.put(observation);registry.deactivate(pack.id)
                            File(context.filesDir,"m4-representations-progress.json").writeText(JSONObject().put("status","RUNNING").put("retrieval_cases",results).put("invalid_imports",invalid).toString(2),Charsets.UTF_8)
                        }
                    }
                }
            }
            assertEquals(6,invalid.length())
            File(context.filesDir,"m4-representations.json").writeText(JSONObject().put("status","PASS").put("fixed_contract_cases",32).put("signed_packs",20)
                .put("retrieval_cases",results).put("invalid_imports",invalid).put("purpose","SYNTHETIC_TRANSLATION_LABELS_NOT_REAL_OFFICIAL_OR_HUMAN_REVIEW")
                .put("developer_trust","EXPLICIT_ISOLATED_TEST_KEYS_NOT_PRODUCTION_DEFAULT").toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));root.deleteRecursively() }
    }

    @Test fun actualRuntimeRendersEnglishAndPreservesCanonicalCitationsOrRejectsBeforeGeneration() {
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext;val assets=instrument.context.assets
        val reference=assets.open("representation-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val public=assets.open("representation-corpus/public-key.raw").use { it.readBytes() };assertEquals(reference.getString("public_key_sha256"),Crypto.sha256(public))
        val root=File(context.filesDir,"representation-runtime-${UUID.randomUUID()}");assertTrue(root.mkdirs());val results=JSONArray()
        try {
            ProductSession(context,File(root,"registry"),listOf(public),true).use { session ->
                val cases=reference.getJSONArray("cases");val records=reference.getJSONArray("packs")
                for(label in listOf("fr-official","ar-reviewed","missing","machine-fr","ambiguous","derived-control","canonical-control","title-control")) {
                    session.registry.snapshot().toList().forEach { session.registry.deactivate(it.id) }
                    val row=(0 until records.length()).map { records.getJSONObject(it) }.single { it.getString("id")==label }
                    val archive=File(root,row.getString("filename"));assets.open("representation-corpus/"+archive.name).use { source -> archive.outputStream().use { source.copyTo(it) } }
                    assertEquals(row.getString("sha256"),Crypto.fileHash(archive));session.registry.activate(archive)
                    val case=(0 until cases.length()).map { cases.getJSONObject(it) }.single { it.getString("id")==label }
                    val trace=session.ask(Query(case.getString("raw"),case.getString("as_of")));val guarded=case.getString("expected_state")!="ANSWER_ACCEPTED"
                    val sources=JSONArray(trace.answer.sources.map { source -> JSONObject().put("id",source.evidenceId).put("canonical_text",source.canonicalText)
                        .put("canonical_language",source.canonicalLanguage ?: JSONObject.NULL).put("canonical_text_sha256",source.canonicalTextSha256 ?: JSONObject.NULL)
                        .put("generator_representation",source.generatorRepresentation?.let { representationJson(it) } ?: JSONObject.NULL) })
                    val observed=JSONObject().put("id",label).put("status","OBSERVED_NOT_ACCEPTANCE").put("state",trace.answer.state)
                        .put("answer",trace.answer.text ?: JSONObject.NULL).put("selected",JSONArray(trace.selected)).put("sources",sources)
                        .put("prefill_tokens",trace.prefillTokens).put("evidence_tokens",trace.evidenceTokens).put("emitted_tokens_including_terminal",trace.emittedTokens)
                        .put("total_ms_including_lazy_initialization",trace.totalMs).put("initialization_ms",trace.initializationMs)
                        .put("actual_weight_inference",!guarded).put("model_load_not_excluded",true)
                    File(context.filesDir,"m4-representation-runtime-observed.json").writeText(observed.toString(2),Charsets.UTF_8)
                    assertEquals(label,case.getString("expected_state"),trace.answer.state)
                    if(guarded) { assertNull(trace.answer.text);assertEquals(0,trace.emittedTokens);assertEquals(0,trace.prefillTokens);assertTrue(trace.selected.isEmpty());assertTrue(trace.answer.sources.isEmpty()) }
                    else {
                        assertTrue(label,trace.answer.text!!.contains("74 °C"));assertFalse(trace.answer.text!!.contains("</think>"));assertEquals(1,trace.answer.sources.size)
                        val source=trace.answer.sources.single();assertEquals(case.getString("canonical_text"),source.canonicalText)
                        assertEquals(case.getString("canonical_language"),source.canonicalLanguage);assertEquals(case.getString("canonical_text_sha256"),source.canonicalTextSha256)
                        assertRepresentation(case.getJSONObject("generator_representation"),representationJson(source.generatorRepresentation!!))
                        assertTrue(trace.prefillTokens<=1536 && trace.evidenceTokens<=1200 && trace.emittedTokens in 1..512)
                    }
                    observed.put("status","PASS");results.put(observed)
                    File(context.filesDir,"m4-representation-runtime-progress.json").writeText(JSONObject().put("status","RUNNING").put("cases",results).toString(2),Charsets.UTF_8)
                }
            }
            File(context.filesDir,"m4-representation-runtime.json").writeText(JSONObject().put("status","PASS").put("cases",results).put("raw_reasoning_persisted",false)
                .put("purpose","ACTUAL_LFM_SYNTHETIC_TRANSLATION_PROTOCOL_NOT_RELEASE_GOLD_REVIEW_CALIBRATION_OR_PERFORMANCE")
                .put("developer_trust","EXPLICIT_ISOLATED_TEST_KEYS_NOT_PRODUCTION_DEFAULT").put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET").toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));root.deleteRecursively() }
    }
}

private fun representationNullable(row:JSONObject,key:String):String?=if(row.isNull(key)) null else row.getString(key)
private fun assertRepresentation(expected:JSONObject,actual:JSONObject) {
    val keys=expected.keys().asSequence().toSet();assertEquals(keys,actual.keys().asSequence().toSet())
    for(key in keys)assertEquals(key,expected.get(key),actual.get(key))
}
private fun representationJson(r:GeneratorRepresentation):JSONObject=JSONObject().put("text",r.text).put("language",r.language)
    .put("text_sha256",r.textSha256).put("derivation_method",r.derivationMethod).put("derivation_source",r.derivationSource ?: JSONObject.NULL)
    .put("reviewer_id",r.reviewerId ?: JSONObject.NULL).put("reviewed_at",r.reviewedAt ?: JSONObject.NULL)
    .put("canonical_language",r.canonicalLanguage).put("canonical_text_sha256",r.canonicalTextSha256)
