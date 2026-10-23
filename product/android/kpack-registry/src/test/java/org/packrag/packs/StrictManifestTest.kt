package org.packrag.packs

import java.io.File
import java.util.zip.ZipFile
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class StrictManifestTest {
    @Test fun sqlNormalizationPreservesLiteralSemantics() {
        assertEquals(DatabaseMetadata.normalizedSql("CREATE TABLE t( a TEXT -- field\n, b INTEGER)"),DatabaseMetadata.normalizedSql("create table t(a text,b integer)"))
        assertNotEquals(DatabaseMetadata.normalizedSql("CHECK(a='ACTIVE')"),DatabaseMetadata.normalizedSql("CHECK(a='active')"))
        assertEquals("check(a='x -- y')",DatabaseMetadata.normalizedSql("CHECK(a='x -- y')"))
    }
    @Test fun sharedManifestSemanticCorpus() {
        val root = File(System.getProperty("packrag.repo"))
        val raw = ZipFile(File(root,"artifacts/v1.3/m1/smoke-0001/developer-pack/walking-skeleton.kpack")).use { zip -> zip.getInputStream(zip.getEntry("manifest.json")).readBytes().toString(Charsets.UTF_8) }
        val profile = JSONObject(raw).getJSONObject("embedding_profile")
        val cases = JSONArray(File(root,"product/tests/manifest-cases.json").readText())
        for (index in 0 until cases.length()) {
            val case = cases.getJSONObject(index); val value = JSONObject(raw)
            if (case.optBoolean("calibrated")) value.put("calibration", JSONObject().put("method","candidate-relevance-v1.3").put("dataset_sha256","a".repeat(64)).put("min_agreed_dense_cosine",0.5).put("min_dense_only_cosine",0.8).put("precision",0.9).put("recall",0.8))
            fun parent(path: JSONArray): Any {
                var current: Any = value
                for (i in 0 until path.length()-1) current = if(current is JSONObject) current.get(path.getString(i)) else (current as JSONArray).get(path.getInt(i))
                return current
            }
            case.optJSONArray("sets")?.let { sets -> for (i in 0 until sets.length()) {
                val set = sets.getJSONArray(i); val path = set.getJSONArray(0); val p = parent(path)
                if(p is JSONObject) p.put(path.getString(path.length()-1),set.get(1)) else (p as JSONArray).put(path.getInt(path.length()-1),set.get(1))
            } }
            case.optJSONArray("removes")?.let { removes -> for (i in 0 until removes.length()) { val path = removes.getJSONArray(i); (parent(path) as JSONObject).remove(path.getString(path.length()-1)) } }
            val failure = runCatching { ManifestSchema.validate(value, profile, case.optBoolean("developer_mode",true)) }.exceptionOrNull()
            if(case.getBoolean("accept")) assertNull(case.getString("id")+": "+failure, failure) else assertNotNull(case.getString("id"),failure)
        }
    }
    @Test fun semverPrecedenceNotLexical() {
        val order = listOf("1.0.0-alpha","1.0.0-alpha.1","1.0.0-alpha.beta","1.0.0-beta","1.0.0-beta.2","1.0.0-beta.11","1.0.0-rc.1","1.0.0","1.0.2","1.0.10","2.0.0")
        order.zipWithNext().forEach { (a,b) -> assertTrue(PackVersion.parse(a)<PackVersion.parse(b)); assertTrue(PackVersion.parse(b)>PackVersion.parse(a)) }
        assertEquals(0,PackVersion.parse("1.0.0+old").compareTo(PackVersion.parse("1.0.0+new")))
        assertTrue(PackVersion.parse("1.0.0-99999999999999999999999") < PackVersion.parse("1.0.0-100000000000000000000000"))
        for (value in listOf("1.0","1.0.0-01","1.0.0+","1.0.0-a..b")) assertThrows(IllegalArgumentException::class.java) { PackVersion.parse(value) }
    }
}
