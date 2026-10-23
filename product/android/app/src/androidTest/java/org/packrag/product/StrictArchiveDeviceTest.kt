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
import org.packrag.packs.ArchivePolicy
import org.packrag.packs.PackVerifier
import org.packrag.model.PortableNames

@RunWith(AndroidJUnit4::class)
class StrictArchiveDeviceTest {
    @Test fun transportAndVerifiedImportParity() {
        val instrument=InstrumentationRegistry.getInstrumentation(); val context=instrument.targetContext; val assets=instrument.context.assets
        val corpus=assets.open("archive-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val key=assets.open("archive-corpus/public-key.raw").use { it.readBytes() }; assertEquals(corpus.getString("public_key_sha256"),Crypto.sha256(key))
        val profile=assets.open("parity-reference.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()).getJSONObject("lock").getJSONObject("embedder").getJSONObject("pack_profile") }
        val schema=assets.open("schema.sql").bufferedReader(Charsets.UTF_8).use { it.readText() }
        assertEquals("ssσffi\u0307",PortableNames.fold("ßςﬀİ")); assertNotEquals(PortableNames.fold("ı"),PortableNames.fold("i"))
        val root=File(context.filesDir,"m3-zip-${UUID.randomUUID()}"); assertTrue(root.mkdirs()); val results=JSONArray()
        try {
            val cases=corpus.getJSONArray("cases")
            for(i in 0 until cases.length()) {
                val case=cases.getJSONObject(i); val archive=File(root,"input.kpack")
                assets.open("archive-corpus/"+case.getString("filename")).use { source -> archive.outputStream().use { source.copyTo(it) } }
                assertEquals(case.getString("sha256"),Crypto.fileHash(archive))
                val auditFailure=runCatching { ArchivePolicy.audit(archive) }.exceptionOrNull()
                assertEquals(case.getString("id")+": audit "+auditFailure,case.getBoolean("audit_accept"),auditFailure==null)
                val stage=File(root,"stage-$i")
                val failure=runCatching { PackVerifier(listOf(key),profile,schema,true).stage(archive,stage) }.exceptionOrNull()
                if(case.getBoolean("accept")) { assertNull(case.getString("id")+": "+failure,failure); assertTrue(stage.deleteRecursively()) }
                else { assertNotNull(case.getString("id"),failure); assertFalse("Rejected ZIP left stage",stage.exists()) }
                assertEquals("Import altered transport",case.getString("sha256"),Crypto.fileHash(archive))
                results.put(JSONObject().put("id",case.getString("id")).put("expected_accept",case.getBoolean("accept")).put("audit_accept",case.getBoolean("audit_accept")).put("passed",true)
                    .put("rejection_class",failure?.javaClass?.name ?: JSONObject.NULL).put("rejection_message",failure?.message?.take(256) ?: JSONObject.NULL))
            }
            File(context.filesDir,"m3-archive-validation.json").writeText(JSONObject().put("status","PASS").put("cases",results).put("corpus",corpus)
                .put("purpose","ACTUAL_ANDROID_LOCAL_CENTRAL_ZIP_AND_AUTHENTICATED_IMPORT_GATE")
                .put("limits","Bounded synthetic fixtures; no exhaustive fuzzing or large-pack peak-memory claim").toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator)); root.deleteRecursively() }
    }
}
