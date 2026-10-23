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
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier

@RunWith(AndroidJUnit4::class)
class ValidationOrderDeviceTest {
    @Test fun independentKdxChecksPrecedeSqliteAndMappingBindsAfterValidatedRows() {
        val instrument=InstrumentationRegistry.getInstrumentation(); val context=instrument.targetContext; val assets=instrument.context.assets
        val corpus=assets.open("validation-order-corpus/cases.json").bufferedReader().use { JSONObject(it.readText()) }
        val key=assets.open("validation-order-corpus/public-key.raw").use { it.readBytes() }; assertEquals(corpus.getString("public_key_sha256"),Crypto.sha256(key))
        val profile=context.assets.open("toolchain.lock.json").bufferedReader().use { JSONObject(it.readText()).getJSONObject("embedder").getJSONObject("pack_profile") }
        val schema=context.assets.open("schema.sql").bufferedReader().use { it.readText() }; val verifier=PackVerifier(listOf(key),profile,schema,true)
        val root=File(context.filesDir,"validation-order-${UUID.randomUUID()}"); assertTrue(root.mkdirs()); val results=JSONArray()
        try {
            val cases=corpus.getJSONArray("cases"); val inputs=(0 until cases.length()).map { index ->
                val case=cases.getJSONObject(index); File(root,case.getString("filename")).also { file ->
                    assets.open("validation-order-corpus/"+file.name).use { source -> file.outputStream().use { source.copyTo(it) } }
                    assertEquals(case.getString("sha256"),Crypto.fileHash(file))
                }
            }
            PackRegistry(File(root,"registry"),verifier).use { registry ->
                val active=registry.activate(inputs.first())
                val original=active.root.walkTopDown().filter { it.isFile }.associate { it.relativeTo(active.root).path to Crypto.fileHash(it) }
                for(i in 0 until cases.length()) {
                    val case=cases.getJSONObject(i); val input=inputs[i]; var failure: Throwable?=null
                    if(case.getBoolean("accept")) {
                        val stage=File(root,"positive-$i"); verifier.stage(input,stage)
                        assertEquals(case.getString("manifest_sha256"),Crypto.fileHash(File(stage,"manifest.json"))); assertTrue(stage.deleteRecursively())
                    } else {
                        failure=runCatching { registry.activate(input) }.exceptionOrNull(); assertNotNull(case.getString("id"),failure)
                        if(!case.isNull("error_contains")) assertTrue(case.getString("id")+": "+failure,originalVerificationCause(failure!!).message.orEmpty().contains(case.getString("error_contains")))
                        else assertTrue(originalVerificationCause(failure!!).message.orEmpty(),originalVerificationCause(requireNotNull(failure)).message.orEmpty().contains("database",ignoreCase=true))
                        assertTrue(File(root,"registry/.staging").listFiles()!!.isEmpty())
                    }
                    assertEquals(listOf(active.id+"@"+active.version),registry.snapshot().map { it.id+"@"+it.version })
                    assertEquals(original,active.root.walkTopDown().filter { it.isFile }.associate { it.relativeTo(active.root).path to Crypto.fileHash(it) })
                    assertEquals(case.getString("sha256"),Crypto.fileHash(input))
                    results.put(JSONObject().put("id",case.getString("id")).put("passed",true).put("accept",case.getBoolean("accept"))
                        .put("before_db",case.getBoolean("before_db")).put("rejection",failure?.message ?: JSONObject.NULL))
                }
            }
            File(context.filesDir,"m3-validation-order.json").writeText(JSONObject().put("status","PASS").put("cases",results)
                .put("prior_active_and_original_hashes_preserved",true).put("failed_staging_cleaned",true).put("caller_inputs_unchanged",true)
                .put("limits","Synthetic signed combined-corruption and norm-boundary fixtures; mapping hash requires validated DB row IDs. No embedding/source truth, release calibration or performance claim.").toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator)); root.deleteRecursively() }
    }
}
