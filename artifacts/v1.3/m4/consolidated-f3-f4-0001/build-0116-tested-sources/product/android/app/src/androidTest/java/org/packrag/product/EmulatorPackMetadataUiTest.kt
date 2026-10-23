package org.packrag.product

import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.v2.createEmptyComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.UUID
import org.packrag.crypto.RawManifestVerifier as Crypto

/** Fill only the missing genuine signed-metadata viewports; no model generation. */
@RunWith(AndroidJUnit4::class)
class EmulatorPackMetadataUiTest {
    @get:Rule val compose=createEmptyComposeRule()
    @Test fun verifiedSignedPublisherKeyVersionAndFullManifestHashAreVisible() {
        val support=ProductUiTestSupport
        val qemu=support.instrument.uiAutomation.executeShellCommand("getprop ro.kernel.qemu")
        assertEquals("1",android.os.ParcelFileDescriptor.AutoCloseInputStream(qemu).bufferedReader().use{it.readText().trim()})
        val ownerNames=listOf("models","packs","production-registry")
        ownerNames.forEach{assertFalse(File(support.context.filesDir,it).exists())}
        val fixture="lifecycle-corpus/v2.kpack"
        val expected=support.instrument.context.assets.open("pack-overview-corpus/expectations.json").bufferedReader()
            .use{JSONObject(it.readText()).getJSONObject("fixtures").getJSONObject(fixture)}
        val input=File(support.context.cacheDir,"emulator-metadata-${UUID.randomUUID()}.kpack")
        val images=JSONObject()
        try {
            support.activity(ProductUiLayout(2f,320),prepare={root ->
                support.instrument.context.assets.open(fixture).use{source->input.outputStream().use{source.copyTo(it)}}
                assertEquals(expected.getString("transport_sha256"),Crypto.fileHash(input))
                ProductSession(support.context,root,ProductConfiguration.keys(support.context),true).use{session ->
                    session.registry.activate(input)
                    session.registry.deactivate(expected.getString("pack_id"))
                }
            }) { _,model ->
                support.ready(compose,model)
                compose.onNodeWithTag("manage-packs").performScrollTo().performClick()
                support.ready(compose,model)
                val row=model.state.value.installed.single()
                assertNotNull(row.overview)
                assertEquals(expected.getString("manifest_sha256"),row.identity.manifestSha256)
                val fields=linkedMapOf(
                    "m4-emulator-signed-publisher.png" to "Publisher: PackRAG DEVELOPMENT ONLY",
                    "m4-emulator-signed-key.png" to "Publisher public key ID: ${expected.getString("publisher_key_id")}",
                    "m4-emulator-signed-version.png" to "Version: ${expected.getString("version")}",
                    "m4-emulator-signed-manifest.png" to "Manifest SHA256: ${expected.getString("manifest_sha256")}")
                val body=compose.onNodeWithTag("product-body")
                for((name,text) in fields) {
                    val target=compose.onNodeWithText(text)
                    target.performScrollTo().assertIsDisplayed()
                    // Repair actual clipping; do not mix outer body bounds with the inner scroll viewport.
                    repeat(4) {
                        val node=target.fetchSemanticsNode()
                        val clipping=node.size.height.toFloat()-node.boundsInRoot.height
                        if(clipping>2f) {
                            val clippedAbove=node.boundsInRoot.top>node.positionInRoot.y+1f
                            val delta=if(clippedAbove) -clipping-32f else clipping+32f
                            body.performSemanticsAction(SemanticsActions.ScrollBy){scroll->assertTrue(scroll(0f,delta))}
                            compose.waitForIdle()
                        }
                    }
                    val settled=target.fetchSemanticsNode()
                    assertEquals("Whole field must be within viewport",settled.size.height.toFloat(),settled.boundsInRoot.height,2f)
                    images.put(name,support.screenshot(compose,name))
                }
            }
            ownerNames.forEach{assertFalse(File(support.context.filesDir,it).exists())}
            File(support.context.filesDir,"m4-emulator-signed-metadata.json").writeText(JSONObject()
                .put("status","PASS").put("emulator_qemu","1").put("actual_weight_inference",false)
                .put("global_font_scale",1).put("raw_reasoning_persisted",false)
                .put("cases",JSONArray(listOf("actual-signed-fixture-and-verified-identity","full-scrolled-publisher-key-version-manifest-fields")))
                .put("visual_png",images).put("transport_sha256",expected.getString("transport_sha256"))
                .put("manifest_sha256",expected.getString("manifest_sha256"))
                .put("scope","Real isolated MainActivity, verified existing DEVELOPMENT synthetic signed pack,2x/320dp emulator. Original PNG review required. No genuine final domain pack/calibration, phone performance, native generation or full M4 claim.")
                .toString(2),Charsets.UTF_8)
        } finally { input.delete() }
    }
}
