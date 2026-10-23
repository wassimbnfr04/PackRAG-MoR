package org.packrag.crypto

import java.io.File
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class JsonSecurityContractTest {
    private val root = File(System.getProperty("packrag.repo"),"artifacts/v1.3/m3/security-fixtures-0001")
    private fun bytes(hex: String) = hex.chunked(2).map { it.toInt(16).toByte() }.toByteArray()
    @Test fun sharedJsonStructureBoundsQuotesEscapesAndDepth() {
        val cases = JSONArray(File(root,"bounds-cases.json").readText())
        for(i in 0 until cases.length()) {
            val case = cases.getJSONObject(i); val raw = case.getString("raw").toByteArray(Charsets.UTF_8)
            val failure = runCatching { JsonBounds.check(raw) }.exceptionOrNull()
            if(case.getBoolean("accept")) assertNull(case.getString("id"),failure) else assertNotNull(case.getString("id"),failure)
        }
    }
    @Test fun signedRawVectorsAndBoundedTrustBeforeStructure() {
        val corpus = JSONObject(File(root,"raw-vectors.json").readText()); val key = bytes(corpus.getString("public_key_hex"))
        val cases = corpus.getJSONArray("cases")
        for(i in 0 until cases.length()) {
            val case = cases.getJSONObject(i)
            val failure = runCatching { RawManifestVerifier.verify(bytes(case.getString("raw_hex")),bytes(case.getString("signature_hex")),listOf(key)) }.exceptionOrNull()
            if(case.getBoolean("accept")) assertNull(case.getString("id"),failure)
            else { assertNotNull(case.getString("id"),failure); if(!case.isNull("error_contains")) assertTrue(case.getString("id")+": "+failure, failure!!.message.orEmpty().contains(case.getString("error_contains"))) }
        }
        val fleet = corpus.getJSONArray("eight_distinct_public_keys_hex").let { a -> (0 until a.length()).map { bytes(a.getString(it)) } }
        val first = cases.getJSONObject(0); val raw = bytes(first.getString("raw_hex")); val sig = bytes(first.getString("signature_hex"))
        assertEquals("1.1.0",RawManifestVerifier.verify(raw,sig,fleet).getString("version"))
        for(keys in listOf(fleet.dropLast(1),fleet+listOf(fleet.first()),fleet.dropLast(1)+listOf(fleet.first()),listOf(key.copyOf(31)),emptyList()))
            assertThrows(IllegalArgumentException::class.java) { RawManifestVerifier.verify(raw,sig,keys) }
    }
}
