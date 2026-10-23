package org.packrag.product

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID
import java.util.zip.ZipEntry
import java.util.zip.ZipFile
import java.util.zip.ZipOutputStream
import kotlin.math.abs
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.embedding.GraniteEncoder
import org.packrag.model.Query
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier
import org.packrag.retrieval.Retrieval

@RunWith(AndroidJUnit4::class)
class PackRetrievalParityTest {
    @Test fun authenticatedActivationRestartAndDesktopRetrievalParity() {
        val instrument = InstrumentationRegistry.getInstrumentation()
        val context = instrument.targetContext
        val assets = instrument.context.assets
        val reference = assets.open("parity-reference.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val lock = reference.getJSONObject("lock").getJSONObject("embedder")
        val profile = lock.getJSONObject("pack_profile")
        val hashes = lock.getJSONObject("asset_sha256")
        val key = assets.open("developer-public-key.raw").use { it.readBytes() }
        val schema = assets.open("schema.sql").bufferedReader(Charsets.UTF_8).use { it.readText() }
        val directory = File(context.filesDir, "m2-retrieval-${UUID.randomUUID()}")
        assertTrue(directory.mkdirs())
        val archive = File(directory, "input.kpack")
        assets.open("walking-skeleton.kpack").use { source -> archive.outputStream().use { source.copyTo(it) } }
        assertEquals(reference.getString("developer_pack_sha256"), Crypto.fileHash(archive))
        val originalHash = Crypto.fileHash(archive)
        val negatives = JSONArray()
        fun rejected(label: String, verifier: PackVerifier, input: File = archive) {
            val stage = File(directory, "rejected-${UUID.randomUUID()}")
            val failure = runCatching { verifier.stage(input, stage) }.exceptionOrNull()
            assertNotNull(label, failure); assertFalse("Failed import left stage", stage.exists())
            negatives.put(JSONObject().put("case", label).put("status", "PASS").put("rejection_class", failure!!.javaClass.name))
        }
        rejected("unknown-signing-key", PackVerifier(listOf(ByteArray(32)), profile, schema, true))
        rejected("uncalibrated-production-import", PackVerifier(listOf(key), profile, schema, false))
        val verifier = PackVerifier(listOf(key), profile, schema, true)
        for (payload in listOf("manifest.sig", "dense.kdx")) {
            val changed = File(directory, "changed-${payload.replace('.', '-')}.kpack")
            ZipFile(archive).use { zip -> ZipOutputStream(changed.outputStream()).use { output ->
                for (entry in zip.entries()) {
                    val bytes = zip.getInputStream(entry).readBytes()
                    if (entry.name == payload) bytes[bytes.lastIndex] = (bytes.last().toInt() xor 1).toByte()
                    output.putNextEntry(ZipEntry(entry.name)); output.write(bytes); output.closeEntry()
                }
            } }
            rejected("tampered-$payload", verifier, changed)
        }
        val results = JSONArray()
        val registryRoot = File(directory, "registry")
        PackRegistry(registryRoot, verifier).use { registry ->
            val pack = registry.activate(archive)
            assertEquals(1, registry.snapshot().size)
            assertThrows(IllegalArgumentException::class.java) { registry.activate(archive) }
            val databaseHash = Crypto.fileHash(File(pack.root, "knowledge.sqlite"))
            GraniteEncoder(File(context.filesDir, "models/granite"), hashes.getString("tokenizer.json"), hashes.getString("onnx/model.onnx")).use { encoder ->
                val cases = reference.getJSONArray("prompt_cases")
                for (index in 0 until cases.length()) {
                    val case = cases.getJSONObject(index)
                    val started = System.nanoTime()
                    val actual = Retrieval.retrieve(registry.snapshot(), Query(case.getString("query"), case.getString("as_of")), encoder.encode(case.getString("query")))
                    assertFalse(actual.ambiguous)
                    val expectedIds = case.getJSONArray("candidate_order")
                    assertEquals(expectedIds.length(), actual.candidates.size)
                    var maxError = 0.0
                    for ((rank, candidate) in actual.candidates.withIndex()) {
                        assertEquals(expectedIds.getString(rank), candidate.chunk.id)
                        assertEquals(nullableRank(case.getJSONArray("sparse_ranks"), rank), candidate.sparseRank)
                        assertEquals(nullableRank(case.getJSONArray("dense_ranks"), rank), candidate.denseRank)
                        assertEquals(case.getJSONArray("rrf").getDouble(rank), candidate.rrf, 1e-12)
                        maxError = maxOf(maxError, abs(case.getJSONArray("dense_cosines").getDouble(rank) - candidate.cosine))
                    }
                    assertTrue("Dense numeric mismatch", maxError <= 1e-4)
                    assertTrue(actual.candidates.first().relevant)
                    results.put(JSONObject().put("id", case.getString("id")).put("status", "PASS")
                        .put("candidate_order", JSONArray(actual.candidates.map { it.chunk.id })).put("max_dense_cosine_error", maxError)
                        .put("embedding_and_retrieval_ms", (System.nanoTime() - started) / 1e6))
                }
                val absent = Retrieval.retrieve(registry.snapshot(), Query("Describe a rainbow dragon", "2026-10-05"), encoder.encode("Describe a rainbow dragon"))
                assertTrue(absent.candidates.none { it.relevant })
            }
            assertEquals(databaseHash, Crypto.fileHash(File(pack.root, "knowledge.sqlite")))
        }
        PackRegistry(registryRoot, verifier).use { reopened -> assertEquals(1, reopened.snapshot().size) }
        assertEquals(originalHash, Crypto.fileHash(archive))
        val output = JSONObject().put("status", "PASS").put("purpose", "M2_PACK_ACTIVATION_RETRIEVAL_PARITY_NOT_GENERATION_ACCEPTANCE")
            .put("source_pack_sha256", originalHash).put("parity_cases", results).put("negative_cases", negatives)
            .put("registry_restart_verified", true).put("original_archive_unchanged", true).put("validated_original_database_unchanged", true)
        File(context.filesDir, "m2-pack-retrieval-parity.json").writeText(output.toString(2), Charsets.UTF_8)
        require(directory.canonicalPath.startsWith(context.filesDir.canonicalPath + File.separator))
        directory.deleteRecursively()
    }
    private fun nullableRank(array: JSONArray, index: Int): Int? = if (array.isNull(index)) null else array.getInt(index)
}
