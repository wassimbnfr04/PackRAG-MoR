package org.packrag.crypto

import java.io.File
import java.util.zip.ZipFile
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class ManifestContractTest {
    @Test fun authenticRawBytesAndBoundedTrustBeforeParsing() {
        val root = File(System.getProperty("packrag.repo"), "artifacts/v1.3/m1/smoke-0001/developer-pack")
        val key = File(root, "developer-public-key.raw").readBytes()
        ZipFile(File(root, "walking-skeleton.kpack")).use { zip ->
            val raw = zip.getInputStream(zip.getEntry("manifest.json")).readBytes()
            val sig = zip.getInputStream(zip.getEntry("manifest.sig")).readBytes()
            assertEquals("org.packrag.development.walking-skeleton", RawManifestVerifier.verify(raw, sig, listOf(key)).getString("pack_id"))
            for ((payload, signature, keys) in listOf(
                Triple(raw + byteArrayOf(32), sig, listOf(key)), Triple(raw, sig.copyOf(63), listOf(key)),
                Triple(raw, sig, listOf(ByteArray(32))), Triple(raw, sig, listOf(key, key)),
                Triple("not JSON".toByteArray(), sig, listOf(key)), Triple(raw, sig, emptyList()),
                Triple(raw, sig, List(9) { key }), Triple(raw, sig, listOf(key.copyOf(31)))
            )) assertThrows(IllegalArgumentException::class.java) { RawManifestVerifier.verify(payload, signature, keys) }
        }
    }
}
