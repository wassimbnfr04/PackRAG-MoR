package org.packrag.week1

import com.google.crypto.tink.subtle.Ed25519Verify
import org.erdtman.jcs.JsonCanonicalizer
import org.json.JSONObject
import java.security.MessageDigest

object RawManifestVerifier {
    fun sha256(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it.toInt() and 255) }
    fun keyId(publicKey: ByteArray) = "ed25519:" + sha256(publicKey)

    fun verify(rawManifest: ByteArray, signature: ByteArray, pinnedKeys: List<ByteArray>): JSONObject {
        require(rawManifest.size <= 1024 * 1024 && signature.size == 64)
        require(pinnedKeys.size in 1..8 && pinnedKeys.all { it.size == 32 })
        require(pinnedKeys.map(::keyId).distinct().size == pinnedKeys.size)
        // Select cryptographically before parsing any untrusted publisher/key metadata.
        val signers = pinnedKeys.filter { key ->
            try { Ed25519Verify(key).verify(signature, rawManifest); true }
            catch (_: java.security.GeneralSecurityException) { false }
        }
        require(signers.size == 1) { "Unknown signer or invalid signature" }
        val manifest = JSONObject(rawManifest.toString(Charsets.UTF_8))
        require(manifest.getJSONObject("publisher").getString("key_id") == keyId(signers.single()))
        // Canonicalization is a post-authentication format check, never the signed message.
        require(JsonCanonicalizer(rawManifest.toString(Charsets.UTF_8)).encodedUTF8.contentEquals(rawManifest))
        require(manifest.getString("schema_version") == "1.0")
        require(manifest.getString("compatible_retrieval_profile") == "mobile-v1")
        require(manifest.getJSONObject("embedding_profile").getString("profile_id") == "granite97m-multi-r2-384-v1")
        return manifest
    }
}
