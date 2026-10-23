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
import org.packrag.packs.ActivePack
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier
import org.packrag.retrieval.Retrieval
import org.packrag.runtime.AdmissionFailure
import org.packrag.runtime.Prompt

@RunWith(AndroidJUnit4::class)
class ConflictDeviceTest {
    @Test fun fixedConflictContractsSignedRetrievalAndActualTokenizerCompanionAdmission() {
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext;val assets=instrument.context.assets
        val reference=assets.open("relevance-reference-corpus/conflict-reference.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        assertEquals(reference.getJSONObject("reference_derivation").getString("previous_reference_sha256"),Crypto.sha256(assets.open("conflict-corpus/cases.json").use { it.readBytes() }))
        val fixed=assets.open("conflict-corpus/conflict-contracts.json").use { it.readBytes() }
        assertEquals(reference.getString("shared_contract_sha256"),Crypto.sha256(fixed))
        assertFixedConflictCases(JSONObject(fixed.toString(Charsets.UTF_8)).getJSONArray("cases"))
        val keys=reference.getJSONArray("public_keys")
        val public=(0 until keys.length()).map { i -> val row=keys.getJSONObject(i)
            assets.open("conflict-corpus/"+row.getString("filename")).use { it.readBytes() }.also { assertEquals(row.getString("sha256"),Crypto.sha256(it)) } }
        val lock=context.assets.open("toolchain.lock.json").bufferedReader().use { JSONObject(it.readText()) }.getJSONObject("embedder")
        val schema=context.assets.open("schema.sql").bufferedReader().use { it.readText() }
        val root=File(context.filesDir,"conflict-parity-${UUID.randomUUID()}");assertTrue(root.mkdirs());val results=JSONArray()
        try {
            PackRegistry(File(root,"registry"),PackVerifier(public,lock.getJSONObject("pack_profile"),schema,true)).use { registry ->
                val packs=linkedMapOf<String,ActivePack>();val records=reference.getJSONArray("packs")
                for(i in 0 until records.length()) {
                    val row=records.getJSONObject(i);val archive=File(root,row.getString("filename"))
                    assets.open("conflict-corpus/"+archive.name).use { source -> archive.outputStream().use { source.copyTo(it) } }
                    assertEquals(row.getString("sha256"),Crypto.fileHash(archive));packs[row.getString("id")]=registry.activate(archive)
                }
                val hashes=lock.getJSONObject("asset_sha256");val models=File(context.filesDir,"models")
                GraniteEncoder(File(models,"granite"),hashes.getString("tokenizer.json"),hashes.getString("onnx/model.onnx")).use { encoder ->
                    LlamaGenerator(File(models,"LFM2.5-2.6B-QAD-Q4_0.gguf"),File(models,"chat_template.jinja"),vocabularyOnly=true).use { tokenizer ->
                        val vectors=mutableMapOf<String,FloatArray>();val cases=reference.getJSONArray("cases")
                        assertEquals(19,cases.length())
                        for(i in 0 until cases.length()) {
                            val case=cases.getJSONObject(i);val label=case.getString("id")
                            val query=Query(case.getString("raw"),case.getString("as_of"),conflictNullable(case,"jurisdiction"),case.getBoolean("current_law"))
                            val vector=vectors.getOrPut(query.normalized) { encoder.encode(query.normalized) }
                            val expectedVector=case.getJSONArray("query_vector");var maxEmbedding=0.0
                            for(j in vector.indices)maxEmbedding=maxOf(maxEmbedding,abs(vector[j]-expectedVector.getDouble(j)))
                            assertTrue(maxEmbedding<=1e-4)
                            val active=conflictStrings(case.getJSONArray("packs")).map { packs.getValue(it) }
                            val actual=Retrieval.retrieve(active,query,vector);assertEquals(label,case.getBoolean("expected_ambiguous"),actual.ambiguous)
                            val reverse=Retrieval.retrieve(active.reversed(),query,vector);assertEquals(label,actual,reverse)
                            val expected=case.getJSONArray("candidates");assertEquals(label,expected.length(),actual.candidates.size);var maxCosine=0.0
                            for((rank,candidate) in actual.candidates.withIndex()) {
                                val row=expected.getJSONObject(rank)
                                assertEquals(label,row.getString("pack_id"),candidate.pack.id);assertEquals(label,row.getString("chunk_id"),candidate.chunk.id)
                                assertEquals(row.getBoolean("exact"),candidate.exact);assertEquals(row.getBoolean("relevant"),candidate.relevant)
                                assertEquals(if(row.isNull("sparse_rank")) null else row.getInt("sparse_rank"),candidate.sparseRank)
                                assertEquals(if(row.isNull("dense_rank")) null else row.getInt("dense_rank"),candidate.denseRank)
                                assertEquals(row.getDouble("rrf"),candidate.rrf,1e-12);maxCosine=maxOf(maxCosine,abs(row.getDouble("cosine")-candidate.cosine))
                                val conflicts=row.getJSONArray("conflicts")
                                assertEquals((0 until conflicts.length()).map { expectedConflict(conflicts.getJSONObject(it)) },candidate.conflicts)
                                val origins=row.getJSONArray("origins")
                                assertEquals((0 until origins.length()).map { j -> val origin=origins.getJSONArray(j)
                                    "${origin.getString(0)}@${origin.getString(1)}:${origin.getString(2)}" },candidate.origins)
                            }
                            assertTrue(label+": cosine",maxCosine<=1e-4)
                            var admission="IDENTIFIER_AMBIGUOUS"
                            val tokens=JSONObject()
                            if(!actual.ambiguous) {
                                if(actual.candidates.none { it.relevant }) admission="NO_RELEVANT_EVIDENCE"
                                else try {
                                    val prepared=Prompt.prepare(query,active,actual.candidates,tokenizer)
                                    assertTrue(prepared.tokens.size<=1536 && prepared.evidenceTokens<=1200 && prepared.evidence.size<=4 && prepared.maximum<=512)
                                    tokens.put("tokens",JSONArray(prepared.tokens.toList())).put("prefill_tokens",prepared.tokens.size)
                                        .put("evidence_tokens",prepared.evidenceTokens).put("max_new",prepared.maximum)
                                        .put("selected",JSONArray(prepared.evidence.map { it.chunk.id }))
                                    admission="READY"
                                } catch(failure:AdmissionFailure) { admission=failure.state }
                            } else if(label=="UNKNOWN") {
                                try { Prompt.prepare(query,active,actual.candidates,tokenizer);fail("Unresolved selected conflict must fail") }
                                catch(failure:AdmissionFailure) { assertEquals("LEGAL_CONFLICT_UNRESOLVED",failure.state) }
                            }
                            assertEquals(label,when { label=="FIVE_COMPANIONS" -> "INCOMPLETE_LEGAL_CONFLICT_EVIDENCE"
                                actual.ambiguous -> "IDENTIFIER_AMBIGUOUS";actual.candidates.isEmpty() -> "NO_RELEVANT_EVIDENCE";else -> "READY" },admission)
                            results.put(JSONObject().put("id",label).put("status","PASS").put("ambiguous",actual.ambiguous).put("candidate_count",actual.candidates.size)
                                .put("max_embedding_abs_error",maxEmbedding).put("max_dense_cosine_error",maxCosine).put("admission",admission)
                                .put("actual_tokenizer",tokens))
                        }
                    }
                }
            }
            File(context.filesDir,"m4-conflicts.json").writeText(JSONObject().put("status","PASS").put("fixed_contract_cases",40).put("signed_packs",19)
                .put("retrieval_cases",results).put("graph_expansion",false).put("global_authority_sort",false)
                .put("actual_tokenizer_companion_admission",true).put("purpose","SYNTHETIC_CONFLICT_METADATA_PARITY_NOT_LEGAL_SOURCE_REVIEW_OR_CALIBRATION")
                .put("developer_trust","EXPLICIT_ISOLATED_TEST_KEYS_NOT_PRODUCTION_DEFAULT").toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));root.deleteRecursively() }
    }
}
