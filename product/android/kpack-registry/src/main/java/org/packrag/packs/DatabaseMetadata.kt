package org.packrag.packs

import androidx.sqlite.SQLiteConnection
import java.io.File
import java.util.Locale
import org.json.JSONObject
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.model.LanguageTags
import org.packrag.model.TemporalDates
import org.packrag.model.normalizeQuery
import org.packrag.model.SourceText

object DatabaseMetadata {
    val tables = listOf("sources","chunks","relations","aliases","derived_texts")
    fun normalizedSql(sql: String): String = Regex("'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|--[^\\n]*|/\\*.*?\\*/|[^\\s]",RegexOption.DOT_MATCHES_ALL)
        .findAll(sql).map { it.value }.filterNot { it.startsWith("--") || it.startsWith("/*") }
        .joinToString("") { if(it.startsWith("'") || it.startsWith("\"")) it else it.lowercase(Locale.ROOT) }
    fun validate(db: SQLiteConnection, manifest: JSONObject, root: File, developerMode: Boolean) {
        val data = tables.associateWith { table ->
            val names = rows(db,"PRAGMA table_info($table)").map { it[1]!! }
            rows(db,"SELECT * FROM $table").map { values -> names.zip(values).toMap() }
        }
        val languages = manifest.getJSONArray("languages").let { a -> (0 until a.length()).map { a.getString(it).lowercase(Locale.ROOT) }.toSet() }
        val jurisdictions = manifest.getJSONArray("jurisdictions").let { a -> (0 until a.length()).map { a.getString(it) }.toSet() }
        val declared = manifest.getJSONArray("files").let { a -> (0 until a.length()).map { a.getJSONObject(it).getString("path") }.toSet() }
        fun text(v: String?) { require(SourceText.nonBlank(v)) { "Empty required DB text" } }
        fun hash(v: String?) { require(v != null && Regex("[0-9a-f]{64}").matches(v)) { "Invalid DB hash" } }
        fun interval(row: Map<String,String?>) {
            val a = row["effective_from"]; val b = row["effective_until_excl"]
            listOfNotNull(a,b).forEach { TemporalDates.date(it) }
            require(a == null || b == null || a < b) { "Invalid DB validity interval" }
        }
        val sourceIds = mutableSetOf<String>(); val chunkIds = mutableSetOf<String>()
        for(row in data.getValue("sources")) {
            listOf("source_id","title","publisher","retrieved_at","language","license","source_type").forEach { text(row[it]) }
            require(sourceIds.add(row["source_id"]!!))
            TemporalDates.dateOrTimestamp(row["retrieved_at"]!!); row["issued_at"]?.let(TemporalDates::dateOrTimestamp)
            interval(row); hash(row["sha256_original"])
            require(LanguageTags.valid(row["language"]!!) && row["language"]!!.lowercase(Locale.ROOT) in languages) { "Undeclared source language" }
            require(row["jurisdiction"] == null || row["jurisdiction"] in jurisdictions) { "Undeclared source jurisdiction" }
            require(row["redistribution_allowed"] in setOf("0","1"))
            row["authority_rank"]?.let { require(it.toLong() in 0..Int.MAX_VALUE.toLong()) }
            require(row["legal_status"] == null || row["legal_status"] in setOf("active","superseded","repealed","historical","n/a"))
            row["snapshot_path"]?.let { path ->
                ArchivePolicy.safePath(path); require(path.startsWith("sources/") && path in declared) { "Invalid snapshot provenance path" }
                require(Crypto.fileHash(File(root,path)) == row["sha256_original"]) { "Snapshot/original source hash mismatch" }
            }
        }
        for(row in data.getValue("chunks")) {
            listOf("chunk_id","source_id","locator","canonical_text","search_text").forEach { text(row[it]) }
            require(chunkIds.add(row["chunk_id"]!!) && row["source_id"] in sourceIds)
            interval(row); hash(row["text_sha256"]); require(Crypto.sha256(row["canonical_text"]!!.toByteArray(Charsets.UTF_8)) == row["text_sha256"])
            for((start,end,minimum) in listOf(Triple("page_start","page_end",1L),Triple("character_start","character_end",0L))) {
                for(key in listOf(start,end)) row[key]?.let { require(it.toLong() in minimum..Int.MAX_VALUE.toLong()) }
                require(row[start] == null || row[end] == null || row[start]!!.toLong() <= row[end]!!.toLong()) { "Reversed DB location bounds" }
            }
        }
        val relationTypes = setOf("parent","child","cites","see_also","amends","supersedes","exception_to","requires","procedure_next","procedure_previous")
        for(row in data.getValue("relations")) {
            require(row["from_chunk_id"] in chunkIds && row["to_chunk_id"] in chunkIds) { "Dangling relation target" }
            require(row["relation_type"] in relationTypes && row["provenance"] in setOf("explicit-reference","structure","curated"))
            val confidence = row["confidence"]!!.toDouble(); require(confidence.isFinite() && confidence in 0.0..1.0)
        }
        for(row in data.getValue("aliases")) {
            listOf("alias","normalized_alias","target_type","target_id","alias_type").forEach { text(row[it]) }
            require(row["normalized_alias"] == normalizeQuery(row["alias"]!!)) { "Noncanonical alias normalization" }
            require(row["target_type"] in setOf("source","chunk"))
            require(row["target_id"] in if(row["target_type"]=="source") sourceIds else chunkIds) { "Dangling alias target" }
        }
        for(row in data.getValue("derived_texts")) {
            listOf("chunk_id","purpose","language","text","text_sha256","derivation_method").forEach { text(row[it]) }
            require(row["chunk_id"] in chunkIds && row["purpose"] == "generator")
            require(LanguageTags.valid(row["language"]!!) && row["language"]!!.lowercase(Locale.ROOT) in languages)
            hash(row["text_sha256"]); require(Crypto.sha256(row["text"]!!.toByteArray(Charsets.UTF_8)) == row["text_sha256"])
            val method = row["derivation_method"]
            require(method in setOf("official_translation","human_reviewed_translation","machine_draft"))
            require(developerMode || method != "machine_draft") { "Machine draft cannot ship as release evidence" }
            if(method != "machine_draft") text(row["derivation_source"])
            if(method == "human_reviewed_translation") { text(row["reviewer_id"]); text(row["reviewed_at"]); TemporalDates.dateOrTimestamp(row["reviewed_at"]!!) }
        }
    }
}
