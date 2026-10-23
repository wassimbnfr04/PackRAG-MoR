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
import org.packrag.model.*
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier
import org.packrag.retrieval.Retrieval

@RunWith(AndroidJUnit4::class)
class ValidityDeviceTest {
    private fun nullable(row:JSONObject,key:String):String?=if(row.isNull(key)) null else row.getString(key)
    private fun chunk(row:JSONObject)=Chunk("c","s","title","source",null,"locator","text","hash","hash",0,
        nullable(row,"jurisdiction"),nullable(row,"source_from"),nullable(row,"source_until"),nullable(row,"effective_from"),
        nullable(row,"effective_until_excl"),nullable(row,"legal_status"),"publisher",null,"en")
    private fun values(v:ValidityProvenance)=mapOf(
        "source_from" to v.sourceFrom,"source_until_excl" to v.sourceUntilExcl,"chunk_from" to v.chunkFrom,"chunk_until_excl" to v.chunkUntilExcl,
        "effective_from" to v.effectiveFrom,"effective_until_excl" to v.effectiveUntilExcl,"source_start_unknown" to v.sourceStartUnknown,
        "source_end_unknown" to v.sourceEndUnknown,"chunk_start_inherits" to v.chunkStartInherits,"chunk_end_inherits" to v.chunkEndInherits,
        "empty_intersection" to v.emptyIntersection,"jurisdiction" to v.jurisdiction,"legal_status" to v.legalStatus)
    private fun checkProvenance(label:String,expected:JSONObject,actual:ValidityProvenance) {
        val map=values(actual);assertEquals(expected.length(),map.size)
        for((key,value) in map) assertEquals(label+":"+key,if(expected.isNull(key)) null else expected.get(key),value)
    }
    @Test fun sharedIntervalsAndSignedEligibleOnlyRetrievalWithActualGranite() {
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext;val assets=instrument.context.assets
        val contract=assets.open("validity-cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val cases=contract.getJSONArray("cases");val contractResults=JSONArray()
        for(i in 0 until cases.length()) {
            val case=cases.getJSONObject(i);val query=Query("question",case.getString("as_of"),nullable(case,"jurisdiction"),case.getBoolean("current_law"))
            assertEquals(case.getString("id"),case.getBoolean("eligible"),eligible(chunk(case.getJSONObject("row")),query))
            contractResults.put(JSONObject().put("id",case.getString("id")).put("status","PASS"))
        }
        val fixed=contract.getJSONArray("provenance_cases")
        for(i in 0 until fixed.length()) { val case=fixed.getJSONObject(i);checkProvenance(case.getString("id"),case.getJSONObject("expected"),validityProvenance(chunk(case.getJSONObject("row")))) }
        val reference=assets.open("validity-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val public=assets.open("validity-corpus/public-key.raw").use { it.readBytes() }
        val lock=context.assets.open("toolchain.lock.json").bufferedReader().use { JSONObject(it.readText()) }.getJSONObject("embedder")
        val schema=context.assets.open("schema.sql").bufferedReader().use { it.readText() }
        val root=File(context.filesDir,"validity-${UUID.randomUUID()}");assertTrue(root.mkdirs());val results=JSONArray()
        try {
            val input=File(root,"input.kpack")
            assets.open("validity-corpus/validity-boundaries.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
            assertEquals(reference.getString("pack_sha256"),Crypto.fileHash(input))
            PackRegistry(File(root,"registry"),PackVerifier(listOf(public),lock.getJSONObject("pack_profile"),schema,true)).use { registry ->
                val pack=registry.activate(input);assertEquals("2020-01-01",pack.manifest.getJSONObject("freshness").getString("update_check_after"))
                val hashes=lock.getJSONObject("asset_sha256")
                GraniteEncoder(File(context.filesDir,"models/granite"),hashes.getString("tokenizer.json"),hashes.getString("onnx/model.onnx")).use { encoder ->
                    val vector=encoder.encode(Query(reference.getString("query_raw"),"2026-01-01").normalized)
                    val expectedVector=reference.getJSONArray("query_vector");var maxError=0.0
                    for(j in vector.indices) maxError=maxOf(maxError,abs(vector[j]-expectedVector.getDouble(j)))
                    assertTrue("actual normalized Granite parity",maxError<=1e-4)
                    val scenarios=reference.getJSONArray("cases")
                    for(i in 0 until scenarios.length()) {
                        val case=scenarios.getJSONObject(i);val label=case.getString("id")
                        val query=Query(reference.getString("query_raw"),case.getString("as_of"),nullable(case,"jurisdiction"),case.getBoolean("current_law"))
                        val allowed=case.getJSONArray("expected_locators");val locators=(0 until allowed.length()).map { allowed.getString(it) }.toSet()
                        assertEquals(label,locators,pack.chunks.filter { eligible(it,query) }.map { it.locator }.toSet())
                        val actual=Retrieval.retrieve(listOf(pack),query,vector);assertEquals(label,case.getBoolean("ambiguous"),actual.ambiguous)
                        assertEquals(label,locators,actual.candidates.map { it.chunk.locator }.toSet())
                        assertEquals((1..actual.candidates.size).toList(),actual.candidates.map { it.denseRank!! }.sorted())
                        val expected=case.getJSONArray("candidates");assertEquals(expected.length(),actual.candidates.size);var maxCosine=0.0
                        for((rank,candidate) in actual.candidates.withIndex()) {
                            val row=expected.getJSONObject(rank);assertEquals(label,row.getString("chunk_id"),candidate.chunk.id)
                            assertTrue(candidate.exact && candidate.relevant)
                            assertEquals(if(row.isNull("sparse_rank")) null else row.getInt("sparse_rank"),candidate.sparseRank)
                            assertEquals(row.getInt("dense_rank"),candidate.denseRank)
                            assertEquals(row.getDouble("rrf"),candidate.rrf,1e-12)
                            maxCosine=maxOf(maxCosine,abs(row.getDouble("cosine")-candidate.cosine))
                            checkProvenance(label,row.getJSONObject("validity"),validityProvenance(candidate.chunk))
                        }
                        assertTrue(label+": cosine",maxCosine<=1e-4)
                        results.put(JSONObject().put("id",label).put("status","PASS").put("eligible_locators",JSONArray(locators.sorted())).put("ambiguous",actual.ambiguous)
                            .put("max_embedding_abs_error",maxError).put("max_dense_cosine_error",maxCosine))
                    }
                }
                assertEquals(reference.getString("pack_sha256"),Crypto.fileHash(input))
            }
            File(context.filesDir,"m4-validity.json").writeText(JSONObject().put("status","PASS").put("purpose","SIGNED_SYNTHETIC_VALIDITY_AND_ACTUAL_GRANITE_PARITY_NOT_REAL_LEGAL_GOLD")
                .put("contract_cases",contractResults).put("fixed_provenance_cases",fixed.length()).put("retrieval_cases",results).put("freshness_not_eligibility",true).toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));root.deleteRecursively() }
    }
}
