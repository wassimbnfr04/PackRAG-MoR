package org.packrag.crypto

import java.io.File
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Test

class ApprovedPublishersContractTest {
    @Test fun sharedPublicStoreContractAndRawAmbiguities() {
        val root=File(System.getProperty("packrag.repo"))
        val cases=JSONArray(File(root,"artifacts/v1.3/m3/release-trust-fixtures-0001/store-cases.json").readText())
        for(i in 0 until cases.length()) {
            val case=cases.getJSONObject(i)
            val failure=runCatching { ApprovedPublishers.keys(case.getJSONObject("value").toString().toByteArray()) }.exceptionOrNull()
            if(case.getBoolean("accept")) assertNull(case.getString("id"),failure) else assertNotNull(case.getString("id"),failure)
        }
        for(raw in listOf(byteArrayOf(),byteArrayOf(0xff.toByte()),ByteArray(65537){32},"{\"schema_version\":\"1.0\",\"schema_version\":\"1.0\"}".toByteArray(),"{".toByteArray(),("[".repeat(33)+"]".repeat(33)).toByteArray()))
            assertNotNull(runCatching { ApprovedPublishers.keys(raw) }.exceptionOrNull())
        val public=File(root,"product/config/release-trust.json").readBytes()
        assertEquals(1,ApprovedPublishers.keys(public).size)
        assertArrayEquals(public,File(root,"product/android/app/src/main/assets/release-trust.json").readBytes())
    }
}
