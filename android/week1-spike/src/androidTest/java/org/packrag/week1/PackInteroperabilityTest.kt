package org.packrag.week1

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.json.JSONObject
import java.io.File

@RunWith(AndroidJUnit4::class)
class PackInteroperabilityTest {
    @Test fun rawSignatureAndReadOnlyEvidenceQuery() {
        val context=InstrumentationRegistry.getInstrumentation().targetContext
        val publicKey=context.assets.open("public_key.raw").use { it.readBytes() }
        val raw=context.assets.open("manifest.json").use { it.readBytes() }
        val sig=context.assets.open("manifest.sig").use { it.readBytes() }
        RawManifestVerifier.verify(raw,sig,listOf(publicKey))
        val wrong=publicKey.copyOf().apply { this[0]=(this[0].toInt() xor 1).toByte() }
        val modified=sig.copyOf().apply { this[0]=(this[0].toInt() xor 1).toByte() }
        assertThrows(IllegalArgumentException::class.java) { RawManifestVerifier.verify(raw,sig,listOf(wrong)) }
        assertThrows(IllegalArgumentException::class.java) { RawManifestVerifier.verify(raw,modified,listOf(publicKey)) }
        assertThrows(IllegalArgumentException::class.java) { RawManifestVerifier.verify(raw,sig,emptyList()) }
        assertThrows(IllegalArgumentException::class.java) { RawManifestVerifier.verify(raw+byteArrayOf(32),sig,listOf(publicKey)) }
        assertThrows(IllegalArgumentException::class.java) { RawManifestVerifier.verify(raw,sig.copyOf(63),listOf(publicKey)) }
        val pack=File(context.filesDir,"week1.kpack")
        context.assets.open("week1.kpack").use { input -> pack.outputStream().use { input.copyTo(it) } }
        val result=KPackSpikeVerifier(listOf(publicKey)).verifyAndQuery(pack,File(context.filesDir,"stage-${System.nanoTime()}"),"Aster-9")
        assertEquals("FOUND_REQUIRES_EVIDENCE_ADMISSION",result.getString("status"))
        assertTrue(result.getJSONArray("chunks").getJSONObject(0).getString("canonical_text").contains("74 °C"))
        File(context.filesDir,"android_verification_results.json").writeText(result.put("android_signature_verify",true).put("android_query",true).put("signature_negative_cases_passed",5).toString(2))
    }
}
