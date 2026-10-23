package org.packrag.week1

import org.junit.Assert.*
import org.junit.Test
import java.io.File

class SignatureVectorTest {
    private val directory = File("../../tests/signature_vector")
    @Test fun pythonSignsTinkVerifies() {
        val raw = File(directory,"manifest.json").readBytes()
        val sig = File(directory,"manifest.sig").readBytes()
        val pub = File(directory,"public_key.raw").readBytes()
        assertEquals("org.packrag.synthetic.week1",RawManifestVerifier.verify(raw,sig,listOf(pub)).getString("pack_id"))
        val wrong = pub.copyOf().apply { this[0] = (this[0].toInt() xor 1).toByte() }
        val badSignature = sig.copyOf().apply { this[0] = (this[0].toInt() xor 1).toByte() }
        for ((message,signature,keys) in listOf(Triple(raw,sig,listOf(wrong)),Triple(raw+byteArrayOf(32),sig,listOf(pub)),Triple(raw,badSignature,listOf(pub)),Triple(raw,sig.copyOf(63),listOf(pub)),Triple(raw,sig,emptyList<ByteArray>()))) {
            assertThrows(IllegalArgumentException::class.java) { RawManifestVerifier.verify(message,signature,keys) }
        }
    }
    @Test fun bufferedCitationValidation() {
        assertNull(OutputValidator.acceptedBody("74 C",setOf("S1")))
        assertNull(OutputValidator.acceptedBody("74 C [S9]",setOf("S1")))
        assertEquals("74 C [S1]",OutputValidator.acceptedBody("74 C [S1]",setOf("S1")))
    }
}
