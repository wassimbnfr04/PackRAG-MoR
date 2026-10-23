package org.packrag.packs

import java.math.BigInteger
import org.json.JSONArray
import org.json.JSONObject
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.model.LanguageTags
import org.packrag.model.TemporalDates
import org.packrag.model.PortableNames

/** SemVer precedence ignores build metadata and compares numeric identifiers numerically. */
class PackVersion private constructor(val core: List<BigInteger>, val pre: List<String>) : Comparable<PackVersion> {
    override fun compareTo(other: PackVersion): Int {
        for (i in 0..2) { val c = core[i].compareTo(other.core[i]); if (c != 0) return c }
        if (pre.isEmpty() || other.pre.isEmpty()) return when { pre == other.pre -> 0; pre.isEmpty() -> 1; else -> -1 }
        for (i in 0 until minOf(pre.size, other.pre.size)) {
            val a = pre[i]; val b = other.pre[i]
            val an = a.all(Char::isDigit); val bn = b.all(Char::isDigit)
            val c = when { an && bn -> a.toBigInteger().compareTo(b.toBigInteger()); an -> -1; bn -> 1; else -> a.compareTo(b) }
            if (c != 0) return c
        }
        return pre.size.compareTo(other.pre.size)
    }
    companion object {
        private val pattern = Regex("(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)(?:-([0-9A-Za-z-]+(?:\\.[0-9A-Za-z-]+)*))?(?:\\+([0-9A-Za-z-]+(?:\\.[0-9A-Za-z-]+)*))?")
        fun parse(value: String): PackVersion {
            val match = pattern.matchEntire(value) ?: throw IllegalArgumentException("Invalid SemVer")
            val pre = match.groupValues[4].takeIf { it.isNotEmpty() }?.split('.') ?: emptyList()
            require(pre.none { it.all(Char::isDigit) && it.length > 1 && it.startsWith('0') }) { "Leading zero in prerelease" }
            return PackVersion((1..3).map { match.groupValues[it].toBigInteger() }, pre)
        }
    }
}

/** Runs only after raw-signature authentication. No org.json coercing getters for field types. */
object ManifestSchema {
    private val hash = Regex("[0-9a-f]{64}")
    private fun fields(value: JSONObject, required: Set<String>, optional: Set<String> = emptySet()) {
        val keys = value.keys().asSequence().toSet()
        require(keys.containsAll(required) && keys.all { it in required + optional }) { "Manifest fields mismatch" }
    }
    private fun text(value: JSONObject, key: String): String {
        val item = value.get(key); require(item is String && item.isNotBlank()) { "Invalid string: $key" }; return item
    }
    private fun obj(value: JSONObject, key: String): JSONObject = value.get(key).also { require(it is JSONObject) { "Invalid object: $key" } } as JSONObject
    private fun integer(value: JSONObject, key: String, max: Long): Long {
        val item = value.get(key); require(item is Int || item is Long) { "Invalid integer: $key" }
        return (item as Number).toLong().also { require(it in 0..max) { "Integer out of range: $key" } }
    }
    private fun array(value: JSONObject, key: String, nonempty: Boolean): List<String> {
        val item = value.get(key); require(item is JSONArray && item.length() <= 5000) { "Invalid array: $key" }
        val result = (0 until item.length()).map { val v = item.get(it); require(v is String && v.isNotBlank()); v }
        require((!nonempty || result.isNotEmpty()) && result.distinct().size == result.size)
        return result
    }
    fun validate(manifest: JSONObject, expectedProfile: JSONObject, developerMode: Boolean) {
        fields(manifest, setOf("schema_version", "pack_id", "name", "version", "release_timestamp", "publisher", "languages", "jurisdictions", "domain", "freshness", "embedding_profile", "compatible_retrieval_profile", "generator_compatibility", "counts", "calibration", "build", "files"))
        require(text(manifest, "schema_version") == "1.0")
        val packId = text(manifest,"pack_id")
        require(Regex("[a-z0-9]+(?:[.-][a-z0-9]+)+").matches(packId) && packId.toByteArray(Charsets.UTF_8).size <= 255) { "Pack ID exceeds portable installation component" }
        text(manifest, "name"); text(manifest, "domain")
        val version = text(manifest,"version")
        require(version.toByteArray(Charsets.UTF_8).size <= 255) { "Version exceeds portable installation component" }
        PackVersion.parse(version)
        val release = text(manifest, "release_timestamp")
        TemporalDates.utc(release)
        val publisher = obj(manifest, "publisher"); fields(publisher, setOf("name", "key_id")); text(publisher, "name")
        require(Regex("ed25519:[0-9a-f]{64}").matches(text(publisher, "key_id")))
        val languages = array(manifest, "languages", true)
        require(languages.all(LanguageTags::valid) && languages.map { it.lowercase(java.util.Locale.ROOT) }.distinct().size == languages.size)
        require(array(manifest, "jurisdictions", false).all { Regex("[A-Z]{2}(?:-[A-Z0-9]{1,3})?").matches(it) })
        val fresh = obj(manifest, "freshness"); fields(fresh, setOf("update_check_after", "stale_behavior"))
        TemporalDates.date(text(fresh, "update_check_after")); require(text(fresh, "stale_behavior") == "warn-and-continue")
        require(Crypto.canonical(obj(manifest, "embedding_profile").toString()).contentEquals(Crypto.canonical(expectedProfile.toString())))
        require(text(manifest, "compatible_retrieval_profile") == "mobile-v1")
        val generator = obj(manifest, "generator_compatibility"); fields(generator, setOf("core_api", "preferred_generator_language", "neural_cache_required"))
        require(text(generator, "core_api") == "1.x" && text(generator, "preferred_generator_language") == "en" && generator.get("neural_cache_required") == false)
        val counts = obj(manifest, "counts"); fields(counts, setOf("sources", "chunks", "relations"))
        for (key in listOf("sources", "chunks", "relations")) integer(counts, key, Int.MAX_VALUE.toLong())
        val calibration = obj(manifest, "calibration")
        fields(calibration, setOf("dataset_sha256", "method", "min_agreed_dense_cosine", "min_dense_only_cosine", "precision", "recall"), setOf("status"))
        require(text(calibration, "method") == "candidate-relevance-v1.3")
        val status = if (calibration.has("status")) text(calibration, "status") else "CALIBRATED"
        require(status in setOf("UNCALIBRATED", "CALIBRATED"))
        require(developerMode || status != "UNCALIBRATED") { "Uncalibrated pack requires developer mode" }
        val metrics = listOf("min_agreed_dense_cosine", "min_dense_only_cosine", "precision", "recall")
        if (status == "UNCALIBRATED") {
            require((metrics + "dataset_sha256").all { calibration.get(it) === JSONObject.NULL }) { "Uncalibrated values must be null" }
        } else {
            require(hash.matches(text(calibration, "dataset_sha256")))
            for (key in metrics) { val v = calibration.get(key); require(v is Number); val n = v.toDouble()
                require(n.isFinite() && n >= (if (key.endsWith("cosine")) -1.0 else 0.0) && n <= 1.0) { "Invalid calibration range" } }
        }
        val build = obj(manifest, "build")
        fields(build, setOf("builder_version", "normalizer_version", "chunker_version", "source_manifest_sha256"), setOf("build_input_sha256"))
        for (key in listOf("builder_version", "normalizer_version", "chunker_version")) text(build, key)
        for (key in listOf("source_manifest_sha256", "build_input_sha256")) if (build.has(key)) require(hash.matches(text(build, key)))
        val files = manifest.get("files"); require(files is JSONArray && files.length() in 2..4998)
        val names = mutableListOf<String>(); var total = 0L
        for (index in 0 until files.length()) {
            val file = files.get(index); require(file is JSONObject)
            fields(file, setOf("path", "sha256", "bytes", "media_type", "required"))
            val path = text(file, "path"); ArchivePolicy.safePath(path); require(path !in ArchivePolicy.controls); names.add(path)
            require(hash.matches(text(file, "sha256"))); total += integer(file, "bytes", ArchivePolicy.MAX_ENTRY)
            require(file.get("required") is Boolean)
            require(Regex("[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+").matches(text(file, "media_type")))
            ArchivePolicy.allowedMediaType(path,text(file,"media_type"))
            if (path in setOf("knowledge.sqlite", "dense.kdx")) require(file.get("required") == true)
        }
        require(total <= ArchivePolicy.MAX_TOTAL && names == names.sortedWith(PortableNames.order) && names.map(PortableNames::fold).distinct().size == names.size)
        require(names.containsAll(setOf("knowledge.sqlite", "dense.kdx")))
    }
}
