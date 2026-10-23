package org.packrag.packs

import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class DataTypeContractTest {
    @Test fun sharedSignedDataTypePathsAndMediaContract() {
        val root=File(System.getProperty("packrag.repo"))
        for (folder in listOf("data-type-fixtures-0001","extension-name-fixtures-0001")) {
        val cases=JSONObject(File(root,"artifacts/v1.3/m3/$folder/cases.json").readText()).getJSONArray("cases")
        for(i in 0 until cases.length()) {
            val case=cases.getJSONObject(i); val path=case.getString("path")
            assertEquals(case.getString("id"),case.getBoolean("path_accept"),runCatching { ArchivePolicy.safePath(path) }.isSuccess)
            assertEquals(case.getString("id"),case.getBoolean("accept"),runCatching { ArchivePolicy.allowedMediaType(path,case.getString("media_type")) }.isSuccess)
        }
        }
    }
}
