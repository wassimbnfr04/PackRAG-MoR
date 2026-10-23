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
import org.packrag.model.Query
import org.packrag.model.QueryUnicode
import org.packrag.model.normalizeQuery
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier
import org.packrag.retrieval.Retrieval

@RunWith(AndroidJUnit4::class)
class QueryIdentifierDeviceTest {
    @Test fun sharedQueryContractsAndSignedNormalizedGraniteMultiPackParity() {
        val instrument=InstrumentationRegistry.getInstrumentation(); val context=instrument.targetContext; val assets=instrument.context.assets
        val contract=assets.open("query-contract-cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val queryCases=contract.getJSONArray("query_cases"); val queryResults=JSONArray()
        for(i in 0 until queryCases.length()) {
            val case=queryCases.getJSONObject(i)
            val outcome=runCatching { Query(case.getString("raw"),case.getString("as_of"),if(case.isNull("jurisdiction")) null else case.getString("jurisdiction"),case.getBoolean("current_law")) }
            if(case.getBoolean("accept")) { assertTrue(case.getString("id"),outcome.isSuccess); assertEquals(case.getString("raw"),outcome.getOrThrow().raw) }
            else { assertTrue(case.getString("id"),outcome.isFailure); assertEquals(case.getString("error"),outcome.exceptionOrNull()!!.message) }
            queryResults.put(JSONObject().put("id",case.getString("id")).put("status","PASS"))
        }
        val wordCases=contract.getJSONArray("word_cases")
        for(i in 0 until wordCases.length()) { val case=wordCases.getJSONObject(i); val expected=case.getJSONArray("terms"); assertEquals((0 until expected.length()).map { expected.getString(it) },QueryUnicode.wordTerms(normalizeQuery(case.getString("raw")))) }
        val aliasCases=contract.getJSONArray("alias_cases")
        for(i in 0 until aliasCases.length()) { val case=aliasCases.getJSONObject(i); assertEquals(case.getBoolean("matched"),QueryUnicode.containsAlias(normalizeQuery(case.getString("text")),normalizeQuery(case.getString("alias")))) }
        val reference=assets.open("relevance-reference-corpus/query-reference.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        assertEquals(reference.getJSONObject("reference_derivation").getString("previous_reference_sha256"),Crypto.sha256(assets.open("query-identifier-corpus/cases.json").use { it.readBytes() }))
        assertEquals(reference.getString("unicode_table_sha256"),QueryUnicode.TABLE_SHA256)
        val public=assets.open("query-identifier-corpus/public-key.raw").use { it.readBytes() }
        val lock=context.assets.open("toolchain.lock.json").bufferedReader().use { JSONObject(it.readText()) }.getJSONObject("embedder")
        val schema=context.assets.open("schema.sql").bufferedReader().use { it.readText() }
        val root=File(context.filesDir,"query-identifiers-${UUID.randomUUID()}"); assertTrue(root.mkdirs())
        val results=JSONArray()
        try {
            PackRegistry(File(root,"registry"),PackVerifier(listOf(public),lock.getJSONObject("pack_profile"),schema,true)).use { registry ->
                val packs=reference.getJSONArray("packs")
                for(i in 0 until packs.length()) {
                    val record=packs.getJSONObject(i); val archive=File(root,record.getString("filename"))
                    assets.open("query-identifier-corpus/"+archive.name).use { source -> archive.outputStream().use { source.copyTo(it) } }
                    assertEquals(record.getString("sha256"),Crypto.fileHash(archive)); registry.activate(archive)
                }
                val active=registry.snapshot().associateBy { it.id.removePrefix("org.packrag.contract.") }
                val hashes=lock.getJSONObject("asset_sha256")
                GraniteEncoder(File(context.filesDir,"models/granite"),hashes.getString("tokenizer.json"),hashes.getString("onnx/model.onnx")).use { encoder ->
                    val cases=reference.getJSONArray("cases")
                    for(i in 0 until cases.length()) {
                        val case=cases.getJSONObject(i); val query=Query(case.getString("raw"),case.getString("as_of"))
                        assertEquals(case.getString("normalized"),query.normalized)
                        val vector=encoder.encode(query.normalized); val expectedVector=case.getJSONArray("query_vector")
                        var maxEmbeddingError=0.0
                        for(j in vector.indices) maxEmbeddingError=maxOf(maxEmbeddingError,abs(vector[j]-expectedVector.getDouble(j)))
                        assertTrue(case.getString("id")+": embedding",maxEmbeddingError<=1e-4)
                        val names=case.getJSONArray("packs"); val selected=(0 until names.length()).map { active.getValue(names.getString(it)) }
                        val actual=Retrieval.retrieve(selected,query,vector); val expected=case.getJSONArray("candidates")
                        assertEquals(case.getString("id"),case.getBoolean("expected_ambiguous"),actual.ambiguous)
                        assertEquals(case.getString("id"),expected.length(),actual.candidates.size)
                        var maxDenseError=0.0
                        for((rank,candidate) in actual.candidates.withIndex()) {
                            val row=expected.getJSONObject(rank)
                            assertEquals(case.getString("id")+" pack rank $rank",row.getString("pack_id"),candidate.pack.id)
                            assertEquals(case.getString("id")+" chunk rank $rank",row.getString("chunk_id"),candidate.chunk.id)
                            assertEquals(row.getBoolean("exact"),candidate.exact); assertEquals(row.getBoolean("relevant"),candidate.relevant)
                            fun nullableRank(name:String):Int? = if(row.isNull(name)) null else row.getInt(name)
                            assertEquals(nullableRank("sparse_rank"),candidate.sparseRank); assertEquals(nullableRank("dense_rank"),candidate.denseRank)
                            assertEquals(row.getDouble("rrf"),candidate.rrf,1e-12)
                            maxDenseError=maxOf(maxDenseError,abs(row.getDouble("dense_cosine")-candidate.cosine))
                            val origins=row.getJSONArray("origins")
                            val expectedOrigins=(0 until origins.length()).map { val o=origins.getJSONArray(it); "${o.getString(0)}@${o.getString(1)}:${o.getString(2)}" }
                            assertEquals(expectedOrigins,candidate.origins); assertEquals(candidate.origins.distinct(),candidate.origins)
                        }
                        assertTrue(case.getString("id")+": cosine",maxDenseError<=1e-4)
                        val reversed=Retrieval.retrieve(selected.reversed(),query,vector)
                        assertEquals(actual.ambiguous,reversed.ambiguous)
                        assertEquals(actual.candidates.map { Triple(it.pack.id,it.chunk.id,it.origins) },reversed.candidates.map { Triple(it.pack.id,it.chunk.id,it.origins) })
                        results.put(JSONObject().put("id",case.getString("id")).put("status","PASS").put("ambiguous",actual.ambiguous)
                            .put("candidate_count",actual.candidates.size).put("candidate_order",JSONArray(actual.candidates.map { "${it.pack.id}:${it.chunk.id}" }))
                            .put("max_embedding_abs_error",maxEmbeddingError).put("max_dense_cosine_error",maxDenseError))
                    }
                }
            }
            File(context.filesDir,"m4-query-identifiers.json").writeText(JSONObject().put("status","PASS").put("purpose","SIGNED_SYNTHETIC_NORMALIZED_ACTUAL_GRANITE_PARITY_NOT_GENERATION_OR_RELEASE_CALIBRATION")
                .put("query_contract_cases",queryResults).put("word_cases",wordCases.length()).put("alias_boundary_cases",aliasCases.length())
                .put("signed_packs",reference.getJSONArray("packs")).put("retrieval_cases",results).put("graph_enabled",false).put("second_rrf",false).toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator)); root.deleteRecursively() }
    }
}
