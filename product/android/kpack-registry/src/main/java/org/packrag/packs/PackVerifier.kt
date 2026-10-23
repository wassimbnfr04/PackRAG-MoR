package org.packrag.packs

import androidx.sqlite.SQLiteConnection
import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import androidx.sqlite.driver.bundled.SQLITE_OPEN_READONLY
import androidx.sqlite.driver.bundled.SQLITE_OPEN_READWRITE
import java.io.File
import java.io.FileOutputStream
import java.util.zip.ZipFile
import org.packrag.model.PortableNames
import java.util.zip.CRC32
import org.json.JSONArray
import org.json.JSONObject
import org.packrag.crypto.RawManifestVerifier as Crypto

internal fun rows(db: SQLiteConnection, sql: String): List<List<String?>> = db.prepare(sql).use { statement ->
    buildList { while (statement.step()) add((0 until statement.getColumnCount()).map {
        if (statement.isNull(it)) null else statement.getText(it)
    }) }
}
internal fun execute(db: SQLiteConnection, sql: String) { db.prepare(sql).use { it.step() } }

/** Format validation for M2 activation. Full hostile-format/lifecycle audit is M3. */
class PackVerifier(private val keys: List<ByteArray>, private val expectedProfile: JSONObject,
                   private val schema: String, private val developerMode: Boolean) {
    fun stage(archive: File, directory: File, observer:(PackImportEvent)->Unit={}): JSONObject {
        val observation=PackImportObservation(observer)
        require(!directory.exists() && directory.mkdirs())
        try {
            // Audit and read one app-owned snapshot, never a replaceable caller path.
            val snapshot = File(directory, "transport.kpack")
            observation.checked(PackImportStage.SNAPSHOT_COPY) { progress ->
            archive.inputStream().use { source -> FileOutputStream(snapshot).use { target ->
                val buffer = ByteArray(65536); var copied = 0L
                while (true) { val count = source.read(buffer); if (count < 0) break
                    copied += count; require(copied <= ArchivePolicy.MAX_TOTAL + 1024 * 1024)
                    target.write(buffer, 0, count);progress(copied)
                }
                target.fd.sync()
            } }
            }
            observation.checked(PackImportStage.ARCHIVE_AUDIT) { ArchivePolicy.audit(snapshot) }
            ZipFile(snapshot).use { zip ->
                lateinit var raw:ByteArray;lateinit var signature:ByteArray
                val manifest = observation.checked(PackImportStage.SIGNATURE_AUTHENTICATION) {
                    raw=read(zip,"manifest.json",1024L*1024);signature=read(zip,"manifest.sig",64)
                    Crypto.verify(raw,signature,keys)
                }
                observation.checked(PackImportStage.MANIFEST_PROFILE_POLICY) {
                ManifestSchema.validate(manifest, expectedProfile, developerMode)
                require(manifest.keys().asSequence().toSet() == setOf("schema_version", "pack_id", "name", "version", "release_timestamp", "publisher", "languages", "jurisdictions", "domain", "freshness", "embedding_profile", "compatible_retrieval_profile", "generator_compatibility", "counts", "calibration", "build", "files"))
                require(manifest.getString("schema_version") == "1.0")
                require(Regex("[a-z0-9]+(?:[.-][a-z0-9]+)+").matches(manifest.getString("pack_id")))
                require(Regex("(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)(?:-[0-9A-Za-z.-]+)?(?:\\+[0-9A-Za-z.-]+)?").matches(manifest.getString("version")))
                require(manifest.getString("compatible_retrieval_profile") == "mobile-v1")
                require(Crypto.canonical(manifest.getJSONObject("embedding_profile").toString()).contentEquals(Crypto.canonical(expectedProfile.toString())))
                val generator = manifest.getJSONObject("generator_compatibility")
                require(generator.keys().asSequence().toSet() == setOf("core_api", "preferred_generator_language", "neural_cache_required"))
                require(generator.getString("core_api") == "1.x" && generator.getString("preferred_generator_language") == "en" && !generator.getBoolean("neural_cache_required"))
                val calibration = manifest.getJSONObject("calibration")
                require(calibration.keys().asSequence().toSet().all { it in setOf("status", "dataset_sha256", "method", "min_agreed_dense_cosine", "min_dense_only_cosine", "precision", "recall") })
                require(developerMode || calibration.optString("status") != "UNCALIBRATED")
                }
                val declared = mutableSetOf<String>()
                val files = manifest.getJSONArray("files")
                var total = 0L
                val ordered = ArrayList<String>()
                val payloadTotal=(0 until files.length()).sumOf { files.getJSONObject(it).getLong("bytes") }
                observation.checked(PackImportStage.PAYLOAD_INTEGRITY,payloadTotal) { progress ->
                var copiedPayload=0L
                for (index in 0 until files.length()) {
                    val file = files.getJSONObject(index)
                    require(file.keys().asSequence().toSet() == setOf("path", "sha256", "bytes", "media_type", "required"))
                    val path = file.getString("path"); ArchivePolicy.safePath(path)
                    require(path !in ArchivePolicy.controls && declared.add(path))
                    ordered.add(path)
                    val length = file.getLong("bytes"); require(length in 0..ArchivePolicy.MAX_ENTRY)
                    total += length; require(total <= ArchivePolicy.MAX_TOTAL)
                    require(Regex("[0-9a-f]{64}").matches(file.getString("sha256")))
                    val target = File(directory, path)
                    require(target.canonicalPath.startsWith(directory.canonicalPath + File.separator))
                    target.parentFile!!.mkdirs()
                    val entry = zip.getEntry(path) ?: error("Missing declared payload")
                    require(entry.size == length)
                    zip.getInputStream(entry).use { source ->
                        FileOutputStream(target).use { output ->
                            val buffer = ByteArray(65536); var written = 0L; val crc = CRC32()
                            while (true) {
                                val count = source.read(buffer); if (count < 0) break
                                written += count; require(written <= length); crc.update(buffer, 0, count); output.write(buffer, 0, count);copiedPayload+=count;progress(copiedPayload)
                            }
                            require(written == length && crc.value == entry.crc) { "Payload CRC/size mismatch" }; output.fd.sync()
                        }
                    }
                    require(Crypto.fileHash(target) == file.getString("sha256")) { "Payload hash mismatch: $path" }
                }
                require(ordered == ordered.sortedWith(PortableNames.order) && ordered.map(PortableNames::fold).distinct().size == ordered.size)
                require(declared.containsAll(setOf("knowledge.sqlite", "dense.kdx")))
                require(zip.entries().asSequence().map { it.name }.toSet() == declared + ArchivePolicy.controls)
                }
                observation.checked(PackImportStage.DATABASE_INDEX) {
                val original = File(directory, "knowledge.sqlite")
                val before = Crypto.fileHash(original)
                val mappingHash = KdxFormat.inspect(File(directory,"dense.kdx"),manifest.getJSONObject("embedding_profile"),manifest.getJSONObject("counts").getInt("chunks"))
                val ids = validateDatabase(original, manifest)
                require(Crypto.fileHash(original) == before) { "Validated DB original mutated" }
                require(mappingHash == Crypto.sha256(Crypto.canonical(JSONArray(ids).toString()))) { "KDX profile/mapping hash mismatch" }
                }
                File(directory, "manifest.json").writeBytes(raw)
                File(directory, "manifest.sig").writeBytes(signature)
                return manifest
            }
        } catch (error: Throwable) {
            require(directory.canonicalPath.startsWith(directory.parentFile!!.canonicalPath + File.separator))
            directory.deleteRecursively()
            throw error
        }
    }

    private fun read(zip: ZipFile, name: String, maximum: Long): ByteArray {
        val entry = zip.getEntry(name) ?: error("Missing control")
        require(entry.size in 0..maximum)
        return zip.getInputStream(entry).use { stream ->
            val output = java.io.ByteArrayOutputStream()
            val buffer = ByteArray(65536); var total = 0L; val crc = CRC32()
            while (true) { val count = stream.read(buffer); if (count < 0) break
                total += count; require(total <= maximum); crc.update(buffer, 0, count); output.write(buffer, 0, count) }
            require(total == entry.size && crc.value == entry.crc) { "Control CRC/size mismatch" }
            output.toByteArray()
        }
    }

    private fun validateDatabase(original: File, manifest: JSONObject): List<String> {
        val copy = File(original.parentFile, "validation.sqlite")
        original.copyTo(copy, overwrite = false)
        try {
            BundledSQLiteDriver().open(copy.absolutePath, SQLITE_OPEN_READWRITE).use { db ->
                execute(db, "PRAGMA trusted_schema=OFF")
                require(rows(db, "PRAGMA integrity_check") == listOf(listOf("ok")))
                require(rows(db, "PRAGMA foreign_key_check").isEmpty())
                val allowed = setOf("sources", "chunks", "chunks_fts", "relations", "aliases", "derived_texts", "aliases_norm_idx", "chunks_fts_data", "chunks_fts_idx", "chunks_fts_docsize", "chunks_fts_config")
                require(rows(db, "SELECT type,name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").all { it[0] in setOf("table", "index") && it[1] in allowed })
                BundledSQLiteDriver().open(":memory:").use { expected ->
                    schema.split(';').map { it.trim() }.filter { it.isNotEmpty() }.forEach { execute(expected, it) }
                    val objectSql = "SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
                    val actualObjects = rows(db,objectSql); val expectedObjects = rows(expected,objectSql)
                    require(actualObjects.map { it.take(2) }.toSet() == expectedObjects.map { it.take(2) }.toSet()) { "Unexpected/missing DB object" }
                    for(name in DatabaseMetadata.tables + listOf("chunks_fts","aliases_norm_idx")) {
                        val actualSql = actualObjects.single { it[1] == name }[2]!!
                        val expectedSql = expectedObjects.single { it[1] == name }[2]!!
                        require(DatabaseMetadata.normalizedSql(actualSql) == DatabaseMetadata.normalizedSql(expectedSql)) { "Full DB schema mismatch: $name" }
                    }
                    for (table in listOf("sources", "chunks", "relations", "aliases", "derived_texts")) {
                        val columns = rows(expected,"PRAGMA table_info($table)")
                        require(rows(db, "PRAGMA table_info($table)") == columns) { "Schema mismatch: $table" }
                        require(rows(db, "PRAGMA foreign_key_list($table)") == rows(expected, "PRAGMA foreign_key_list($table)"))
                        val types = rows(db,"SELECT " + columns.joinToString(",") { "typeof(${it[1]})" } + " FROM $table")
                        for(values in types) for((index,column) in columns.withIndex()) {
                            val accepted = when(column[2]) { "TEXT" -> setOf("text"); "INTEGER" -> setOf("integer"); "REAL" -> setOf("real","integer"); else -> error("Unexpected application schema type") }
                            require(values[index] == "null" || values[index] in accepted) { "DB storage type mismatch" }
                        }
                    }
                    val fts = rows(db, "SELECT sql FROM sqlite_master WHERE name='chunks_fts'").single().single()!!
                        .replace(Regex("\\s+"), "").lowercase(java.util.Locale.ROOT)
                    require("usingfts5(" in fts && "content='chunks'" in fts && "content_rowid='rowid'" in fts && "tokenize='unicode61remove_diacritics2'" in fts)
                }
                execute(db, "INSERT INTO chunks_fts(chunks_fts,rank) VALUES('integrity-check',1)")
                for (table in listOf("sources", "chunks", "relations")) require(rows(db, "SELECT count(*) FROM $table").single().single()!!.toInt() == manifest.getJSONObject("counts").getInt(table))
                require(rows(db,"SELECT count(*) FROM chunks_fts").single().single()!!.toInt() == manifest.getJSONObject("counts").getInt("chunks"))
                val mapping = rows(db, "SELECT chunk_id,dense_row,canonical_text,text_sha256 FROM chunks ORDER BY dense_row")
                require(mapping.map { it[1]!!.toInt() } == mapping.indices.toList())
                require(mapping.all { Crypto.sha256(it[2]!!.toByteArray(Charsets.UTF_8)) == it[3] })
                DatabaseMetadata.validate(db,manifest,original.parentFile!!,developerMode)
                return mapping.map { it[0]!! }
            }
        } finally { require(copy.delete()) }
    }

}
