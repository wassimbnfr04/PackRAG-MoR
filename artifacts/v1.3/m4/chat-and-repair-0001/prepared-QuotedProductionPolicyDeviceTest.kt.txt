package org.packrag.product

import androidx.test.ext.junit.runners.AndroidJUnit4
import java.io.File
import java.nio.file.Files
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.generator.GenerationPolicy

/** Current compiled-policy regression with original generated device report preserved. */
@RunWith(AndroidJUnit4::class)
class QuotedProductionPolicyDeviceTest {
    @Test fun matchedCompiledPolicyPreservesHistoricalReportAndOwnerFiles() {
        val context=ProductUiTestSupport.context
        val before=ChatRepairOwner.snapshot();assertEquals(51,before.size)
        val policy=GenerationPolicy.quotes(context.assets.open("generation-profile-quotes-v1.json").use{it.readBytes()})
        val original=File(context.filesDir,"m3-production-policy.json")
        assertFalse(Files.isSymbolicLink(original.toPath()))
        if(original.exists())assertTrue(original.isFile && original.length()<=1024*1024)
        val previous=if(original.exists())original.readBytes() else null
        var report:JSONObject?=null
        try {
            // Reuse every unchanged original strict policy assertion; no copied/relaxed fixture expectations.
            ProductionPolicyDeviceTest().compiledDemoPolicyAndActualViewModelAdmissionHaveNoDevelopmentBypass()
            report=JSONObject(original.readText(Charsets.UTF_8));assertEquals("PASS",report!!.getString("status"))
        } finally {
            if(previous!=null)original.writeBytes(previous) else if(original.exists())assertTrue(original.delete())
        }
        if(previous!=null)assertArrayEquals(previous,original.readBytes()) else assertFalse(original.exists())
        val after=ChatRepairOwner.snapshot();assertEquals(before,after)
        val result=requireNotNull(report).put("current_generation_profile_id",policy.profileId)
            .put("current_generation_config_sha256",policy.configSha256).put("original_test_report_restored",true)
            .put("owner_sha256_before",JSONObject(before)).put("owner_sha256_after",JSONObject(after))
            .put("actual_model_inference",false)
        File(context.filesDir,"m4-quoted-production-policy-0001.json").writeText(result.toString(2),Charsets.UTF_8)
    }
}
