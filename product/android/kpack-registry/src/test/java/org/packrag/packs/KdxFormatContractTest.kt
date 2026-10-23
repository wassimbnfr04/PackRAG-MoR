package org.packrag.packs

import java.io.File
import java.nio.file.Files
import java.util.zip.ZipFile
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class KdxFormatContractTest {
    @Test fun sharedIndependentStructureAndDoubleNormBoundaries() {
        val root=File(requireNotNull(System.getProperty("packrag.repo")),"artifacts/v1.3/m3/validation-order-fixtures-0001")
        val cases=JSONObject(File(root,"cases.json").readText()).getJSONArray("cases")
        val temporary=Files.createTempDirectory("kdx-contract-").toFile()
        try {
            for(i in 0 until cases.length()) {
                val case=cases.getJSONObject(i)
                ZipFile(File(root,case.getString("filename"))).use { zip ->
                    val manifest=JSONObject(zip.getInputStream(zip.getEntry("manifest.json")).readBytes().toString(Charsets.UTF_8))
                    val file=File(temporary,"dense.kdx"); file.writeBytes(zip.getInputStream(zip.getEntry("dense.kdx")).readBytes())
                    val failure=runCatching { KdxFormat.inspect(file,manifest.getJSONObject("embedding_profile"),manifest.getJSONObject("counts").getInt("chunks")) }.exceptionOrNull()
                    if(case.getBoolean("before_db")) { assertNotNull(case.getString("id"),failure); assertTrue(failure!!.message.orEmpty().contains(case.getString("error_contains"))) }
                    else assertNull(case.getString("id"),failure)
                }
            }
        } finally { temporary.deleteRecursively() }
    }
}
