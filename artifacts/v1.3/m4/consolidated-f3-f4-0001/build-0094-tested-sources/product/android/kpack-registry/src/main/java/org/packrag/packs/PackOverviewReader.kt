package org.packrag.packs

import java.io.File
import org.json.JSONObject
import org.packrag.model.PackIdentity
import org.packrag.model.PackOverview

/** The caller holds the complete authenticated private snapshot until primitives are copied. */
internal fun readPackOverview(root:File,manifest:JSONObject,identity:PackIdentity):PackOverview {
    val publisher=manifest.getJSONObject("publisher")
    val files=manifest.getJSONArray("files")
    return PackOverview(identity,manifest.getString("name"),publisher.getString("name"),publisher.getString("key_id"),
        manifest.getJSONObject("freshness").getString("update_check_after"),File(root,"manifest.json").length(),
        (0 until files.length()).sumOf { files.getJSONObject(it).getLong("bytes") },File(root,"transport.kpack").length())
}
