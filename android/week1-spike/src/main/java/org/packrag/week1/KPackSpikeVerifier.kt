package org.packrag.week1

import androidx.sqlite.SQLiteConnection
import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import androidx.sqlite.driver.bundled.SQLITE_OPEN_READONLY
import androidx.sqlite.driver.bundled.SQLITE_OPEN_READWRITE
import org.erdtman.jcs.JsonCanonicalizer
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.text.Normalizer
import java.util.Locale
import java.util.zip.ZipFile
import kotlin.math.abs
import kotlin.math.sqrt

/** Developer smoke importer. No production registry/activation or hybrid retrieval. */
class KPackSpikeVerifier(private val pinnedKeys: List<ByteArray>) {
    private fun safePath(path: String) {
        require(path.isNotEmpty() && !path.startsWith('/') && '\\' !in path && ':' !in path)
        require(Normalizer.normalize(path,Normalizer.Form.NFC) == path)
        val reserved = Regex("(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\\..*)?")
        for (part in path.split('/')) {
            require(part !in listOf("", ".", "..") && !part.endsWith('.') && !part.endsWith(' '))
            require(part.none { it.code < 32 || it in "<>\"|?*" } && !reserved.matches(part))
        }
        require(path in setOf("manifest.json","manifest.sig","knowledge.sqlite","dense.kdx") || path.startsWith("sources/"))
        require(File(path).extension.lowercase() !in setOf("exe","dll","so","py","js","sh","bat","cmd","ps1","jar","dex","apk","sql","gguf","onnx","pt","safetensors"))
    }

    // ZipFile hides Unix external attributes. Inspect central records before extraction.
    private fun auditCentral(file: File) {
        RandomAccessFile(file,"r").use { input ->
            require(input.length() >= 22)
            val tailSize = minOf(input.length(),65557).toInt()
            val tail = ByteArray(tailSize); input.seek(input.length()-tailSize); input.readFully(tail)
            val view = ByteBuffer.wrap(tail).order(ByteOrder.LITTLE_ENDIAN)
            val end = (tailSize-22 downTo 0).firstOrNull { view.getInt(it)==0x06054b50 } ?: error("Missing ZIP central directory")
            require(end+22+(view.getShort(end+20).toInt() and 65535)==tailSize)
            require(view.getShort(end+4).toInt()==0 && view.getShort(end+6).toInt()==0)
            val count=view.getShort(end+10).toInt() and 65535
            require(count <= 5000 && (view.getShort(end+8).toInt() and 65535)==count)
            val offset=view.getInt(end+16).toLong() and 0xffffffffL
            var total=0L; val seen=mutableSetOf<String>(); input.seek(offset)
            repeat(count) {
                val record=ByteArray(46); input.readFully(record); val r=ByteBuffer.wrap(record).order(ByteOrder.LITTLE_ENDIAN)
                require(r.getInt(0)==0x02014b50)
                val flags=r.getShort(8).toInt() and 65535; val method=r.getShort(10).toInt() and 65535
                require(flags and 1 == 0 && method in setOf(0,8))
                val size=r.getInt(24).toLong() and 0xffffffffL; require(size<=256L*1024*1024)
                total+=size; require(total<=512L*1024*1024)
                val mode=(r.getInt(38) ushr 16) and 0xf000; require(mode==0 || mode==0x8000)
                val length=r.getShort(28).toInt() and 65535; val name=ByteArray(length);input.readFully(name)
                val path=name.toString(Charsets.UTF_8);safePath(path)
                require(seen.add(path.lowercase(Locale.ROOT))) { "Duplicate ZIP name" }
                input.skipBytes((r.getShort(30).toInt() and 65535)+(r.getShort(32).toInt() and 65535))
            }
        }
    }

    private fun boundedRead(zip: ZipFile,name: String,max: Long): ByteArray {
        require(max in 0..(256L*1024*1024))
        val entry=zip.getEntry(name) ?: error("Missing payload")
        require(entry.size in 0..max)
        zip.getInputStream(entry).use { stream ->
            val output=java.io.ByteArrayOutputStream();val buffer=ByteArray(65536);var count=0L
            while (true) { val n=stream.read(buffer);if(n<0)break;count+=n;require(count<=max);output.write(buffer,0,n) }
            return output.toByteArray()
        }
    }

    fun verifyAndQuery(pack: File, stage: File, identifier: String): JSONObject {
        auditCentral(pack);require(!stage.exists());require(stage.mkdirs())
        try {
            ZipFile(pack).use { zip ->
                val raw=boundedRead(zip,"manifest.json",1024*1024)
                val manifest=RawManifestVerifier.verify(raw,boundedRead(zip,"manifest.sig",64),pinnedKeys)
                require(manifest.getJSONObject("calibration").getString("status")=="UNCALIBRATED") { "This spike only accepts the developer fixture" }
                val files=manifest.getJSONArray("files");val declared=mutableSetOf("manifest.json","manifest.sig")
                for (i in 0 until files.length()) {
                    val f=files.getJSONObject(i);val path=f.getString("path");safePath(path);require(declared.add(path))
                    val data=boundedRead(zip,path,f.getLong("bytes"))
                    require(data.size.toLong()==f.getLong("bytes") && RawManifestVerifier.sha256(data)==f.getString("sha256"))
                    val target=File(stage,path);require(target.canonicalPath.startsWith(stage.canonicalPath+File.separator))
                    target.parentFile!!.mkdirs();target.outputStream().use { it.write(data) }
                }
                require(zip.entries().asSequence().map { it.name }.toSet()==declared)
                val dbFile=File(stage,"knowledge.sqlite");val before=RawManifestVerifier.sha256(dbFile.readBytes())
                val ids=validateDatabase(dbFile,manifest)
                require(RawManifestVerifier.sha256(dbFile.readBytes())==before)
                auditKdx(File(stage,"dense.kdx"),manifest.getJSONObject("embedding_profile"),ids)
                BundledSQLiteDriver().open(dbFile.absolutePath,SQLITE_OPEN_READONLY).use { db ->
                    val results=JSONArray()
                    db.prepare("SELECT c.chunk_id,c.canonical_text,c.locator FROM aliases a JOIN chunks c ON a.target_id=c.chunk_id WHERE a.normalized_alias=? AND a.target_type='chunk' ORDER BY c.chunk_id").use { stmt ->
                        stmt.bindText(1,Normalizer.normalize(identifier,Normalizer.Form.NFKC).lowercase(Locale.ROOT).trim())
                        while(stmt.step())results.put(JSONObject().put("chunk_id",stmt.getText(0)).put("canonical_text",stmt.getText(1)).put("locator",stmt.getText(2)))
                    }
                    return JSONObject().put("status",if(results.length()>1)"AMBIGUOUS_IDENTIFIER" else if(results.length()==1)"FOUND_REQUIRES_EVIDENCE_ADMISSION" else "INSUFFICIENT_EVIDENCE")
                        .put("chunks",results).put("manifest_sha256",RawManifestVerifier.sha256(raw)).put("algorithm","week1_identifier_smoke_only")
                }
            }
        } finally { stage.deleteRecursively() }
    }

    private fun rows(db: SQLiteConnection,sql: String): List<List<String>> = db.prepare(sql).use { s ->
        buildList { while(s.step()) add((0 until s.getColumnCount()).map { if(s.isNull(it)) "NULL" else s.getText(it) }) }
    }

    private fun validateDatabase(original: File,manifest: JSONObject): List<String> {
        val copy=File(original.parentFile,"validation.sqlite");original.copyTo(copy,overwrite=false)
        try {
            BundledSQLiteDriver().open(copy.absolutePath,SQLITE_OPEN_READWRITE).use { db ->
                db.prepare("PRAGMA trusted_schema=OFF").use { it.step() }
                require(rows(db,"PRAGMA integrity_check")==listOf(listOf("ok")))
                require(rows(db,"PRAGMA foreign_key_check").isEmpty())
                val allowed=setOf("sources","chunks","chunks_fts","relations","aliases","derived_texts","aliases_norm_idx","chunks_fts_data","chunks_fts_idx","chunks_fts_docsize","chunks_fts_config")
                require(rows(db,"SELECT type,name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").all { it[0] in setOf("table","index") && it[1] in allowed })
                for ((table,columns) in expectedColumns) {
                    require(rows(db,"PRAGMA table_info($table)").map { it[1] }==columns) { "Schema mismatch $table" }
                }
                db.prepare("INSERT INTO chunks_fts(chunks_fts,rank) VALUES('integrity-check',1)").use { it.step() }
                for (table in listOf("sources","chunks","relations")) require(rows(db,"SELECT count(*) FROM $table").single().single().toInt()==manifest.getJSONObject("counts").getInt(table))
                val mapping=rows(db,"SELECT chunk_id,dense_row,canonical_text,text_sha256 FROM chunks ORDER BY dense_row")
                require(mapping.map { it[1].toInt() }==mapping.indices.toList())
                require(mapping.all { RawManifestVerifier.sha256(it[2].toByteArray(Charsets.UTF_8))==it[3] })
                return mapping.map { it[0] }
            }
        } finally { require(copy.delete()) }
    }

    private fun auditKdx(file: File,profile: JSONObject,ids: List<String>) {
        val data=file.readBytes();require(data.size>=84);val b=ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN)
        val magic=ByteArray(8);b.get(magic);require(magic.contentEquals(byteArrayOf(75,68,88,49,0,0,0,0)))
        require(b.short.toInt()==1 && b.get().toInt()==1 && b.get().toInt()==1 && b.short.toInt()==384 && b.short.toInt()==1)
        val count=b.int;require(count==ids.size && data.size.toLong()==84L+count*384L*4)
        val ph=ByteArray(32);b.get(ph);val mh=ByteArray(32);b.get(mh)
        fun hex(a: ByteArray)=a.joinToString(""){"%02x".format(it.toInt() and 255)}
        require(hex(ph)==RawManifestVerifier.sha256(JsonCanonicalizer(profile.toString()).encodedUTF8))
        require(hex(mh)==RawManifestVerifier.sha256(JsonCanonicalizer(JSONArray(ids).toString()).encodedUTF8))
        repeat(count) { var norm=0.0;repeat(384) { val value=b.float;require(value.isFinite());norm+=value.toDouble()*value };require(abs(sqrt(norm)-1.0)<=0.01) }
    }

    companion object {
        private val expectedColumns=mapOf(
            "sources" to "source_id title publisher canonical_uri retrieved_at issued_at effective_from effective_until_excl jurisdiction language document_version sha256_original license redistribution_allowed source_type authority_rank legal_status snapshot_path notes".split(' '),
            "chunks" to "rowid chunk_id source_id parent_section_id title section article locator canonical_text search_text text_sha256 page_start page_end character_start character_end effective_from effective_until_excl dense_row".split(' '),
            "relations" to "from_chunk_id to_chunk_id relation_type provenance confidence".split(' '),
            "aliases" to "alias normalized_alias target_type target_id alias_type".split(' '),
            "derived_texts" to "chunk_id purpose language text text_sha256 derivation_method derivation_source reviewer_id reviewed_at".split(' ')
        )
    }
}
