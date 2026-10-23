package org.packrag.product

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID
import java.util.zip.ZipFile
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.crypto.JsonBounds
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier

@RunWith(AndroidJUnit4::class)
class ResidualSecurityDeviceTest {
    private fun bytes(hex: String) = hex.chunked(2).map { it.toInt(16).toByte() }.toByteArray()
    @Test fun signedPayloadHashStructuralKdxAndParserBoundaryGateBeforeActivation() {
        val instrument = InstrumentationRegistry.getInstrumentation(); val context = instrument.targetContext; val assets = instrument.context.assets
        val corpus = assets.open("security-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val key = assets.open("security-corpus/public-key.raw").use { it.readBytes() }; assertEquals(corpus.getString("public_key_sha256"),Crypto.sha256(key))
        val profile = assets.open("parity-reference.json").bufferedReader().use { JSONObject(it.readText()).getJSONObject("lock").getJSONObject("embedder").getJSONObject("pack_profile") }
        val schema = assets.open("schema.sql").bufferedReader().use { it.readText() }; val verifier = PackVerifier(listOf(key),profile,schema,true)
        val root = File(context.filesDir,"m3-security-${UUID.randomUUID()}"); assertTrue(root.mkdirs())
        val cases = corpus.getJSONArray("cases"); val inputs = mutableMapOf<String,File>(); val results = JSONArray(); val rawResults = JSONArray(); val boundsResults = JSONArray()
        try {
            for(i in 0 until cases.length()) {
                val case = cases.getJSONObject(i); val input = File(root,case.getString("filename"))
                assets.open("security-corpus/"+input.name).use { source -> input.outputStream().use { source.copyTo(it) } }
                assertEquals(case.getString("sha256"),Crypto.fileHash(input)); inputs[case.getString("id")] = input
            }
            val baseline = inputs.getValue("valid")
            PackRegistry(File(root,"registry"),verifier).use { registry ->
                val pack = registry.activate(baseline); val identity = pack.id+"@"+pack.version
                val original = pack.root.walkTopDown().filter { it.isFile }.associate { it.relativeTo(pack.root).path to Crypto.fileHash(it) }
                for(i in 0 until cases.length()) {
                    val case = cases.getJSONObject(i); val input = inputs.getValue(case.getString("id")); val stage = File(root,"stage-$i")
                    if(case.getBoolean("accept")) {
                        val manifest = verifier.stage(input,stage); assertEquals(case.getString("manifest_sha256"),Crypto.fileHash(File(stage,"manifest.json")))
                        assertEquals(10,manifest.getJSONObject("counts").getInt("chunks")); assertTrue(stage.deleteRecursively())
                        if(case.getString("group")=="IDENTITY_BOUND") PackRegistry(File(root,"portable-$i"),verifier).use { portable ->
                            val accepted = portable.activate(input); assertEquals(case.getString("manifest_sha256"),accepted.manifestHash); assertTrue(accepted.root.isDirectory)
                        }
                    } else {
                        val failure = runCatching { registry.activate(input) }.exceptionOrNull(); assertNotNull(case.getString("id"),failure)
                        if(!case.isNull("error_contains")) assertTrue(case.getString("id")+": "+failure,failure!!.message.orEmpty().contains(case.getString("error_contains")))
                        assertEquals(listOf(identity),registry.snapshot().map { it.id+"@"+it.version })
                        assertEquals(original,pack.root.walkTopDown().filter { it.isFile }.associate { it.relativeTo(pack.root).path to Crypto.fileHash(it) })
                        assertTrue(File(root,"registry/.staging").listFiles()!!.isEmpty())
                    }
                    assertEquals(case.getString("sha256"),Crypto.fileHash(input))
                    if(case.getString("group")=="HASH_TAMPER") ZipFile(baseline).use { old -> ZipFile(input).use { changed ->
                        assertArrayEquals(old.getInputStream(old.getEntry("manifest.json")).readBytes(),changed.getInputStream(changed.getEntry("manifest.json")).readBytes())
                        assertArrayEquals(old.getInputStream(old.getEntry("manifest.sig")).readBytes(),changed.getInputStream(changed.getEntry("manifest.sig")).readBytes())
                        val payload = if(case.getString("id").contains("knowledge")) "knowledge.sqlite" else "dense.kdx"
                        val a=old.getInputStream(old.getEntry(payload)).readBytes(); val b=changed.getInputStream(changed.getEntry(payload)).readBytes()
                        assertEquals(a.size,b.size); assertEquals(1,a.indices.count { a[it]!=b[it] })
                        val crc=java.util.zip.CRC32(); crc.update(b); assertEquals(crc.value,changed.getEntry(payload).crc)
                    } }
                    results.put(JSONObject().put("id",case.getString("id")).put("passed",true).put("accept",case.getBoolean("accept")))
                }
            }
            val vectors = assets.open("security-corpus/raw-vectors.json").bufferedReader().use { JSONObject(it.readText()) }; val raws = vectors.getJSONArray("cases")
            for(i in 0 until raws.length()) {
                val case = raws.getJSONObject(i); val failure = runCatching { Crypto.verify(bytes(case.getString("raw_hex")),bytes(case.getString("signature_hex")),listOf(key)) }.exceptionOrNull()
                if(case.getBoolean("accept")) assertNull(case.getString("id"),failure)
                else { assertNotNull(case.getString("id"),failure); if(!case.isNull("error_contains")) assertTrue(case.getString("id")+": "+failure,failure!!.message.orEmpty().contains(case.getString("error_contains"))) }
                rawResults.put(JSONObject().put("id",case.getString("id")).put("passed",true))
            }
            val fleet = vectors.getJSONArray("eight_distinct_public_keys_hex").let { a -> (0 until a.length()).map { bytes(a.getString(it)) } }
            val first = raws.getJSONObject(0); val raw = bytes(first.getString("raw_hex")); val sig = bytes(first.getString("signature_hex"))
            assertEquals("1.1.0",Crypto.verify(raw,sig,fleet).getString("version"))
            for(keys in listOf(fleet.dropLast(1),fleet+listOf(fleet.first()),fleet.dropLast(1)+listOf(fleet.first()),listOf(key.copyOf(31)),emptyList())) assertThrows(IllegalArgumentException::class.java) { Crypto.verify(raw,sig,keys) }
            val bounds = assets.open("security-corpus/bounds-cases.json").bufferedReader().use { JSONArray(it.readText()) }
            for(i in 0 until bounds.length()) {
                val case = bounds.getJSONObject(i); val failure = runCatching { JsonBounds.check(case.getString("raw").toByteArray(Charsets.UTF_8)) }.exceptionOrNull()
                if(case.getBoolean("accept")) assertNull(case.getString("id"),failure) else assertNotNull(case.getString("id"),failure)
                boundsResults.put(JSONObject().put("id",case.getString("id")).put("passed",true))
            }
            File(context.filesDir,"m3-residual-security.json").writeText(JSONObject().put("status","PASS").put("cases",results).put("raw_signature_vectors",rawResults).put("json_bounds",boundsResults)
                .put("eight_distinct_keys_and_five_rejected_sets",true).put("prior_active_original_hashes_preserved",true).put("failed_staging_cleaned",true).put("caller_inputs_unchanged",true)
                .put("limits","Synthetic security vectors; no release calibration, source truth or exhaustive fuzzing claim. 255-byte identity components install on this physical filesystem; release publisher trust is a separate gate.").toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator)); root.deleteRecursively() }
    }
}
