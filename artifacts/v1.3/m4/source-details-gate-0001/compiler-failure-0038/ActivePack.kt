package org.packrag.packs

import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import androidx.sqlite.driver.bundled.SQLITE_OPEN_READONLY
import java.io.Closeable
import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteOrder
import java.nio.channels.FileChannel
import org.json.JSONObject
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.model.Chunk
import org.packrag.model.SourceRelation
import org.packrag.model.DerivedText
import org.packrag.model.SourceAttribution
import org.packrag.model.SourceLocation

/** Constructed only after PackVerifier authenticates and validates its owned snapshot. */
class ActivePack internal constructor(val root: File, val manifest: JSONObject) : Closeable {
    val id: String = manifest.getString("pack_id")
    val version: String = manifest.getString("version")
    val manifestHash: String = Crypto.fileHash(File(root, "manifest.json"))
    private val db = BundledSQLiteDriver().open(File(root, "knowledge.sqlite").absolutePath, SQLITE_OPEN_READONLY)
    private val denseFile = RandomAccessFile(File(root, "dense.kdx"), "r")
    private val vectors = if(denseFile.length() == 84L) java.nio.FloatBuffer.allocate(0) else denseFile.channel.map(FileChannel.MapMode.READ_ONLY, 84, denseFile.length() - 84)
        .order(ByteOrder.LITTLE_ENDIAN).asFloatBuffer()
    val chunks: List<Chunk>
    val aliases: List<Alias>
    val relations: List<SourceRelation>
    val derivedByChunk: Map<String,List<DerivedText>>
    val byId: Map<String, Chunk>

    init {
        execute(db, "PRAGMA trusted_schema=OFF"); execute(db, "PRAGMA query_only=ON")
        chunks = rows(db, "SELECT c.chunk_id,c.source_id,c.title,s.title,c.section,c.locator,c.canonical_text,c.text_sha256,s.sha256_original,c.dense_row,s.jurisdiction,s.effective_from,s.effective_until_excl,c.effective_from,c.effective_until_excl,s.legal_status,s.publisher,s.canonical_uri,s.language,s.authority_rank,s.document_version,s.issued_at,c.article,s.retrieved_at,s.license,s.redistribution_allowed,s.source_type,s.snapshot_path,s.notes,c.page_start,c.page_end,c.character_start,c.character_end FROM chunks c JOIN sources s USING(source_id) ORDER BY c.dense_row").map { r ->
            Chunk(r[0]!!, r[1]!!, r[2] ?: "", r[3]!!, r[4], r[5]!!, r[6]!!, r[7]!!, r[8]!!,
                r[9]!!.toInt(), r[10], r[11], r[12], r[13], r[14], r[15], r[16]!!, r[17], r[18]!!,
                r[19]?.toInt(),r[20],r[21],r[22],
                SourceAttribution(r[17],r[23]!!,r[24]!!,r[25]!!=="1",r[26]!!,r[27],r[28]),
                SourceLocation(r[2],r[4],r[29]?.toLong(),r[30]?.toLong(),r[31]?.toLong(),r[32]?.toLong()))
        }
        byId = chunks.associateBy { it.id }
        aliases = rows(db, "SELECT normalized_alias,target_type,target_id FROM aliases").map { Alias(it[0]!!, it[1]!!, it[2]!!) }
        relations = rows(db,"SELECT from_chunk_id,to_chunk_id,relation_type,provenance,confidence FROM relations ORDER BY from_chunk_id,to_chunk_id,relation_type")
            .map { SourceRelation(it[0]!!,it[1]!!,it[2]!!,it[3]!!,it[4]!!.toDouble()) }
        derivedByChunk=rows(db,"SELECT chunk_id,purpose,language,text,text_sha256,derivation_method,derivation_source,reviewer_id,reviewed_at FROM derived_texts ORDER BY chunk_id,purpose,language")
            .map { DerivedText(it[0]!!,it[1]!!,it[2]!!,it[3]!!,it[4]!!,it[5]!!,it[6],it[7],it[8]) }.groupBy { it.chunkId }
    }

    @Synchronized fun sparse(expression: String): List<String> {
        return db.prepare("SELECT c.chunk_id FROM chunks_fts JOIN chunks c ON c.rowid=chunks_fts.rowid WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts) ASC,c.chunk_id ASC").use { statement ->
            statement.bindText(1, expression)
            buildList { while (statement.step()) add(statement.getText(0)) }
        }
    }
    fun cosine(row: Int, query: FloatArray): Double {
        require(query.size == 384 && row in chunks.indices)
        var score = 0.0
        for (index in query.indices) score += vectors.get(row * 384 + index).toDouble() * query[index]
        return score
    }
    @Synchronized override fun close() { db.close(); denseFile.close() }
}

data class Alias(val normalized: String, val targetType: String, val targetId: String)
