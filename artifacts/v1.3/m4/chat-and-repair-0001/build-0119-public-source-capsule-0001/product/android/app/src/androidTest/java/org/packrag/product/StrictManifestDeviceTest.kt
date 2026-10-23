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
import org.packrag.packs.PackVerifier

@RunWith(AndroidJUnit4::class)
class StrictManifestDeviceTest {
    @Test fun signedHostileManifestCorpusAndUntouchedValidPack() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext; val assets = instrumentation.context.assets
        val corpus = assets.open("manifest-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val key = assets.open("manifest-corpus/public-key.raw").use { it.readBytes() }
        assertEquals(corpus.getString("public_key_sha256"),Crypto.sha256(key))
        val profile = assets.open("parity-reference.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()).getJSONObject("lock").getJSONObject("embedder").getJSONObject("pack_profile") }
        val schema = assets.open("schema.sql").bufferedReader(Charsets.UTF_8).use { it.readText() }
        val root = File(context.filesDir,"m3-manifest-${UUID.randomUUID()}"); assertTrue(root.mkdirs())
        val results = JSONArray()
        try {
            val cases = corpus.getJSONArray("cases")
            for (index in 0 until cases.length()) {
                val case = cases.getJSONObject(index); val input = File(root,"input.kpack")
                assets.open("manifest-corpus/"+case.getString("filename")).use { source -> input.outputStream().use { source.copyTo(it) } }
                assertEquals(case.getString("sha256"),Crypto.fileHash(input))
                val stage = File(root,"stage-$index")
                val failure = runCatching { PackVerifier(listOf(key),profile,schema,case.getBoolean("developer_mode")).stage(input,stage) }.exceptionOrNull()
                if (case.getBoolean("accept")) { assertNull(case.getString("id")+": "+failure,failure); assertTrue(stage.exists()); stage.deleteRecursively() }
                else { assertNotNull(case.getString("id"),failure); assertFalse("Failed validation left staging data",stage.exists()) }
                assertEquals("Import changed transport",case.getString("sha256"),Crypto.fileHash(input))
                results.put(JSONObject().put("id",case.getString("id")).put("expected_accept",case.getBoolean("accept")).put("passed",true).put("rejection_class",failure?.javaClass?.name ?: JSONObject.NULL))
            }
            File(context.filesDir,"m3-manifest-schema.json").writeText(JSONObject().put("status","PASS").put("cases",results)
                .put("purpose","ACTUAL_ANDROID_SIGNED_MANIFEST_SCHEMA_AND_ADJACENT_VALID_DB_KDX_GATE")
                .put("calibrated_test_metadata","Synthetic values test schema only; not measured release calibration or human-reviewed40-case proof")
                .put("input_corpus",corpus).toString(2),Charsets.UTF_8)
        } finally {
            require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator)); root.deleteRecursively()
        }
    }
}
