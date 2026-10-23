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
import org.packrag.model.SourceMetadata
import org.packrag.model.sourceMetadata
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier
import org.packrag.retrieval.Retrieval

@RunWith(AndroidJUnit4::class)
class SourceMetadataDeviceTest {
    private fun nullable(row:JSONObject,key:String):String?=if(row.isNull(key)) null else row.getString(key)
    private fun checkMetadata(expected:JSONObject,actual:SourceMetadata) {
        assertEquals(if(expected.isNull("authority_rank")) null else expected.getInt("authority_rank"),actual.authorityRank)
        assertEquals(nullable(expected,"document_version"),actual.documentVersion);assertEquals(nullable(expected,"issued_at"),actual.issuedAt)
        assertEquals(nullable(expected,"article"),actual.article);assertEquals(expected.getString("publisher_key_id"),actual.publisherKeyId)
        val relations=expected.getJSONArray("relations");assertEquals(relations.length(),actual.relations.size)
        for((index,relation) in actual.relations.withIndex()) {
            val row=relations.getJSONObject(index)
            assertEquals(row.getString("from_chunk_id"),relation.fromChunkId);assertEquals(row.getString("to_chunk_id"),relation.toChunkId)
            assertEquals(row.getString("relation_type"),relation.relationType);assertEquals(row.getString("provenance"),relation.provenance)
            assertEquals(row.getDouble("confidence"),relation.confidence,0.0)
        }
    }
    @Test fun authenticatedSourceFieldsDirectedRelationsAndUnchangedRetrievalRules() {
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext;val assets=instrument.context.assets
        val reference=assets.open("source-metadata-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val public=assets.open("source-metadata-corpus/public-key.raw").use { it.readBytes() }
        assertEquals(reference.getString("public_key_sha256"),Crypto.sha256(public))
        val lock=context.assets.open("toolchain.lock.json").bufferedReader().use { JSONObject(it.readText()) }.getJSONObject("embedder")
        val schema=context.assets.open("schema.sql").bufferedReader().use { it.readText() }
        val root=File(context.filesDir,"source-metadata-${UUID.randomUUID()}");assertTrue(root.mkdirs());val metadataResults=JSONArray();val results=JSONArray()
        try {
            val input=File(root,"input.kpack")
            assets.open("source-metadata-corpus/source-metadata.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
            assertEquals(reference.getString("pack_sha256"),Crypto.fileHash(input))
            PackRegistry(File(root,"registry"),PackVerifier(listOf(public),lock.getJSONObject("pack_profile"),schema,true)).use { registry ->
                val pack=registry.activate(input);assertEquals(5,pack.relations.size)
                val expectedMetadata=reference.getJSONArray("metadata_cases")
                for(i in 0 until expectedMetadata.length()) {
                    val row=expectedMetadata.getJSONObject(i);val chunk=pack.byId.getValue(row.getString("chunk_id"))
                    assertEquals("https://example.invalid/synthetic/"+row.getString("locator"),chunk.canonicalUri)
                    checkMetadata(row.getJSONObject("metadata"),sourceMetadata(chunk,pack.manifest.getJSONObject("publisher").getString("key_id"),pack.relations))
                    metadataResults.put(JSONObject().put("locator",row.getString("locator")).put("status","PASS"))
                }
                val hashes=lock.getJSONObject("asset_sha256")
                GraniteEncoder(File(context.filesDir,"models/granite"),hashes.getString("tokenizer.json"),hashes.getString("onnx/model.onnx")).use { encoder ->
                    val vector=encoder.encode(Query(reference.getString("query_raw"),"2026-01-01").normalized)
                    val expectedVector=reference.getJSONArray("query_vector");var maxEmbedding=0.0
                    for(j in vector.indices)maxEmbedding=maxOf(maxEmbedding,abs(vector[j]-expectedVector.getDouble(j)))
                    assertTrue(maxEmbedding<=1e-4)
                    val cases=reference.getJSONArray("retrieval_cases")
                    for(i in 0 until cases.length()) {
                        val case=cases.getJSONObject(i);val label=case.getString("id")
                        val query=Query(reference.getString("query_raw"),case.getString("as_of"),nullable(case,"jurisdiction"),case.getBoolean("current_law"))
                        val actual=Retrieval.retrieve(listOf(pack),query,vector);assertEquals(label,case.getBoolean("ambiguous"),actual.ambiguous)
                        val eligible=case.getJSONArray("expected_locators");val expectedLocators=(0 until eligible.length()).map { eligible.getString(it) }.toSet()
                        assertEquals(label,expectedLocators,actual.candidates.map { it.chunk.locator }.toSet())
                        val expected=case.getJSONArray("candidates");assertEquals(expected.length(),actual.candidates.size);var maxCosine=0.0
                        for((rank,candidate) in actual.candidates.withIndex()) {
                            val row=expected.getJSONObject(rank);assertEquals(label,row.getString("chunk_id"),candidate.chunk.id)
                            assertTrue(candidate.exact && candidate.relevant)
                            assertEquals(if(row.isNull("sparse_rank")) null else row.getInt("sparse_rank"),candidate.sparseRank)
                            assertEquals(row.getInt("dense_rank"),candidate.denseRank);assertEquals(row.getDouble("rrf"),candidate.rrf,1e-12)
                            maxCosine=maxOf(maxCosine,abs(row.getDouble("cosine")-candidate.cosine))
                        }
                        assertTrue(label+": cosine",maxCosine<=1e-4)
                        results.put(JSONObject().put("id",label).put("status","PASS").put("candidate_count",actual.candidates.size)
                            .put("ambiguous",actual.ambiguous).put("max_embedding_abs_error",maxEmbedding).put("max_dense_cosine_error",maxCosine))
                    }
                }
                assertEquals(reference.getString("pack_sha256"),Crypto.fileHash(input))
            }
            File(context.filesDir,"m4-source-metadata.json").writeText(JSONObject().put("status","PASS").put("purpose","SIGNED_SYNTHETIC_SOURCE_METADATA_AND_ACTUAL_GRANITE_PARITY_NOT_AUTHORITY_RESOLUTION")
                .put("metadata_cases",metadataResults).put("directed_relations",5).put("retrieval_cases",results)
                .put("authority_sort",false).put("graph_expansion",false).put("document_heading_policy",reference.getString("document_heading_policy")).toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));root.deleteRecursively() }
    }
}
