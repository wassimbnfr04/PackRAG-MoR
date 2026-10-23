package org.packrag.crypto

import com.google.crypto.tink.subtle.Ed25519Verify
import java.io.File
import java.security.GeneralSecurityException
import java.security.MessageDigest
import org.erdtman.jcs.JsonCanonicalizer
import org.json.JSONObject

object RawManifestVerifier {
    fun sha256(bytes: ByteArray): String = hex(MessageDigest.getInstance("SHA-256").digest(bytes))
    fun hex(bytes: ByteArray): String = bytes.joinToString("") { "%02x".format(it.toInt() and 255) }
    fun fileHash(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { stream ->
            val buffer = ByteArray(65536)
            while (true) { val count = stream.read(buffer); if (count < 0) break; digest.update(buffer, 0, count) }
        }
        return hex(digest.digest())
    }
    fun canonical(json: String): ByteArray = JsonCanonicalizer(json).encodedUTF8
    fun keyId(key: ByteArray): String = "ed25519:" + sha256(key)

    fun verify(raw: ByteArray, signature: ByteArray, pinned: List<ByteArray>): JSONObject {
        require(raw.size in 1..1024 * 1024 && signature.size == 64)
        require(pinned.size in 1..8 && pinned.all { it.size == 32 })
        require(pinned.map(::keyId).distinct().size == pinned.size)
        // No JSON fields are interpreted until exactly one pinned key verifies raw bytes.
        val matched = pinned.filter { key ->
            try { Ed25519Verify(key).verify(signature, raw); true } catch (_: GeneralSecurityException) { false }
        }
        require(matched.size == 1) { "Unknown signer or invalid signature" }
        JsonBounds.check(raw)
        val text = raw.toString(Charsets.UTF_8)
        val canonicalRaw = try { canonical(text) } catch(error: Exception) { throw IllegalArgumentException("Noncanonical signed manifest",error) }
        require(canonicalRaw.contentEquals(raw)) { "Noncanonical signed manifest" }
        val manifest = JSONObject(text)
        require(manifest.getJSONObject("publisher").getString("key_id") == keyId(matched.single())) { "Signer/key_id mismatch" }
        return manifest
    }
}
