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
import org.packrag.model.LanguageTags
import org.packrag.model.TemporalDates
import org.packrag.model.normalizeQuery
import org.packrag.packs.PackVerifier

@RunWith(AndroidJUnit4::class)
class StrictDatabaseDeviceTest {
    @Test fun signedDatabaseNegativesAndFormatParity() {
        val instrument=InstrumentationRegistry.getInstrumentation(); val context=instrument.targetContext; val assets=instrument.context.assets
        val corpus=assets.open("database-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val key=assets.open("database-corpus/public-key.raw").use { it.readBytes() }; assertEquals(corpus.getString("public_key_sha256"),Crypto.sha256(key))
        val profile=assets.open("parity-reference.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()).getJSONObject("lock").getJSONObject("embedder").getJSONObject("pack_profile") }
        val schema=assets.open("schema.sql").bufferedReader(Charsets.UTF_8).use { it.readText() }
        val formats=assets.open("format-cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val formatResults=JSONArray()
        val languages=formats.getJSONArray("languages")
        for(i in 0 until languages.length()) { val c=languages.getJSONArray(i); assertEquals(c.getString(0),c.getBoolean(1),LanguageTags.valid(c.getString(0))); formatResults.put(JSONObject().put("language",c.getString(0)).put("passed",true)) }
        for(group in listOf("dates","timestamps")) {
            val cases=formats.getJSONArray(group)
            for(i in 0 until cases.length()) { val c=cases.getJSONArray(i); val failure=runCatching { if(group=="dates") TemporalDates.date(c.getString(0)) else TemporalDates.utc(c.getString(0)) }.exceptionOrNull()
                if(c.getBoolean(1)) assertNull(c.getString(0)+": "+failure,failure) else assertNotNull(c.getString(0),failure)
                formatResults.put(JSONObject().put("group",group).put("input",c.getString(0)).put("passed",true)) }
        }
        val normalized=formats.getJSONArray("normalization")
        for(i in 0 until normalized.length()) { val c=normalized.getJSONArray(i); assertEquals(c.getString(1),normalizeQuery(c.getString(0))); formatResults.put(JSONObject().put("normalized",c.getString(1)).put("passed",true)) }
        val root=File(context.filesDir,"m3-db-${UUID.randomUUID()}"); assertTrue(root.mkdirs()); val results=JSONArray()
        try {
            val cases=corpus.getJSONArray("cases")
            for(i in 0 until cases.length()) {
                val case=cases.getJSONObject(i); val archive=File(root,"input.kpack")
                assets.open("database-corpus/"+case.getString("filename")).use { source -> archive.outputStream().use { source.copyTo(it) } }
                assertEquals(case.getString("sha256"),Crypto.fileHash(archive)); val stage=File(root,"stage-$i")
                val failure=runCatching { PackVerifier(listOf(key),profile,schema,case.getBoolean("developer_mode")).stage(archive,stage) }.exceptionOrNull()
                if(case.getBoolean("accept")) { assertNull(case.getString("id")+": "+failure,failure); assertFalse(File(stage,"validation.sqlite").exists()); assertTrue(stage.deleteRecursively()) }
                else { assertNotNull(case.getString("id"),failure); assertFalse("Rejected DB left stage",stage.exists()) }
                assertEquals("Validation altered transport",case.getString("sha256"),Crypto.fileHash(archive))
                results.put(JSONObject().put("id",case.getString("id")).put("expected_accept",case.getBoolean("accept")).put("passed",true)
                    .put("rejection_class",failure?.javaClass?.name ?: JSONObject.NULL).put("rejection_message",failure?.message?.take(256) ?: JSONObject.NULL))
            }
            File(context.filesDir,"m3-database-validation.json").writeText(JSONObject().put("status","PASS").put("cases",results).put("format_cases",formatResults)
                .put("purpose","ACTUAL_ANDROID_SIGNED_DB_FTS_METADATA_PROVENANCE_AND_FORMAT_GATE")
                .put("limits","Synthetic translation/reviewer/calibration records test field rules only; no genuine official/human review or release calibration claim")
                .put("corpus",corpus).toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator)); root.deleteRecursively() }
    }
}
