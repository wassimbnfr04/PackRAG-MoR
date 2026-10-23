package org.packrag.packs

import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import androidx.sqlite.driver.bundled.SQLITE_OPEN_READONLY
import java.io.File
import org.json.JSONObject
import org.packrag.model.PackDetails
import org.packrag.model.PackIdentity
import org.packrag.model.PackSourceDetails
import org.packrag.model.SourceAttribution

/** Caller owns a newly authenticated private snapshot until these copied values are returned. */
internal fun readPackDetails(root:File,manifest:JSONObject,identity:PackIdentity):PackDetails {
    val db=BundledSQLiteDriver().open(File(root,"knowledge.sqlite").absolutePath,SQLITE_OPEN_READONLY)
    val sources=try {
        execute(db,"PRAGMA trusted_schema=OFF");execute(db,"PRAGMA query_only=ON")
        rows(db,"SELECT source_id,title,publisher,language,sha256_original,canonical_uri,retrieved_at,license,redistribution_allowed,source_type,snapshot_path,notes,effective_from,effective_until_excl,jurisdiction,legal_status,authority_rank,document_version,issued_at FROM sources ORDER BY source_id").map { r ->
            PackSourceDetails(r[0]!!,r[1]!!,r[2]!!,r[3]!!,r[4]!!,
                SourceAttribution(r[5],r[6]!!,r[7]!!,r[8]!!=="1",r[9]!!,r[10],r[11]),
                r[12],r[13],r[14],r[15],r[16]?.toInt(),r[17],r[18])
        }
    } finally { db.close() }
    fun strings(name:String):List<String> { val array=manifest.getJSONArray(name);return (0 until array.length()).map { array.getString(it) } }
    val files=manifest.getJSONArray("files")
    val publisher=manifest.getJSONObject("publisher");val calibration=manifest.getJSONObject("calibration")
    return PackDetails(identity,manifest.getString("name"),manifest.getString("domain"),publisher.getString("name"),publisher.getString("key_id"),
        manifest.getString("release_timestamp"),manifest.getJSONObject("freshness").getString("update_check_after"),
        strings("languages"),strings("jurisdictions"),manifest.getJSONObject("embedding_profile").toString(),manifest.getJSONObject("build").toString(),
        calibration.toString(),calibration.getString("status"),File(root,"manifest.json").length(),
        (0 until files.length()).sumOf { files.getJSONObject(it).getLong("bytes") },File(root,"transport.kpack").length(),
        manifest.getJSONObject("counts").getInt("chunks"),sources)
}
