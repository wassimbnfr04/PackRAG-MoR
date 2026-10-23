package org.packrag.crypto

import java.nio.ByteBuffer
import java.nio.charset.CodingErrorAction
import org.json.JSONObject

/** Only application-owned configuration supplies this; packs cannot add keys. */
object ApprovedPublishers {
    fun keys(raw: ByteArray): List<ByteArray> {
        require(raw.size in 1..65536) { "Trust store exceeds bounded configuration size" }
        JsonBounds.check(raw)
        val text = Charsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString()
        RawManifestVerifier.canonical(text) // Reject ambiguous duplicate JSON properties.
        val value = JSONObject(text)
        require(value.keys().asSequence().toSet()==setOf("schema_version","approval_scope","publishers")) { "Trust store fields mismatch" }
        require(value.get("schema_version")=="1.0" && value.get("approval_scope")=="packrag-project-demonstrators") { "Unsupported trust store" }
        val entries = value.getJSONArray("publishers"); require(entries.length() in 1..8) { "Trust store must contain1–8 approved publishers" }
        val keys = (0 until entries.length()).map { index ->
            val publisher = entries.getJSONObject(index)
            require(publisher.keys().asSequence().toSet()==setOf("name","key_id","public_key_hex")) { "Publisher fields mismatch" }
            val name = publisher.get("name"); require(name is String && name.isNotBlank()) { "Invalid publisher name" }
            val encoded = publisher.get("public_key_hex"); require(encoded is String && Regex("[0-9a-f]{64}").matches(encoded)) { "Invalid publisher public key" }
            val key = encoded.chunked(2).map { it.toInt(16).toByte() }.toByteArray()
            require(publisher.get("key_id")==RawManifestVerifier.keyId(key)) { "Publisher key identity mismatch" }; key
        }
        require(keys.map(RawManifestVerifier::keyId).distinct().size==keys.size) { "Duplicate approved publisher" }
        return keys
    }
}
