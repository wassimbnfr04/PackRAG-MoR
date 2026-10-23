package org.packrag.product

import android.content.Intent
import android.graphics.Bitmap
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.assertHasClickAction
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.v2.createEmptyComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.ByteBuffer
import java.nio.file.Files
import java.security.MessageDigest
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.model.PackIdentity
import org.packrag.model.PackOverview

/** Pure presentation component controls. The fixed values are intentionally unsigned. */
@RunWith(AndroidJUnit4::class)
class PackOverviewLongUiTest {
    @get:Rule val compose=createEmptyComposeRule()
    private val instrument get()=InstrumentationRegistry.getInstrumentation()
    private val context get()=instrument.targetContext
    private val valuesSha="3a4c243da367b27d10781acd69b7d56e6aa522ce90e3da0ac1d4262d16a51825"
    private fun values():JSONObject {
        val raw=instrument.context.assets.open("pack-overview-corpus/long-presentation-values.json").use { it.readBytes() }
        assertEquals(valuesSha,Crypto.sha256(raw));return JSONObject(raw.toString(Charsets.UTF_8))
    }
    private fun row(v:JSONObject):PackRow {
        val identity=PackIdentity(v.getString("pack_id"),v.getString("version"),v.getString("manifest_sha256"))
        val owned=PackOverview(identity,v.getString("name"),v.getString("publisher_name"),v.getString("publisher_key_id"),
            v.getString("update_check_after"),v.getLong("manifest_bytes"),v.getLong("payload_bytes"),v.getLong("transport_bytes"))
        return PackRow(identity.packId,identity.version,identity.manifestSha256,"VERIFIED",true,null,null,owned)
    }
    private fun foreground(){assertEquals("org.packrag.product",instrument.uiAutomation.rootInActiveWindow?.packageName?.toString())}
    private fun frame(content:@Composable ()->Unit,assertions:()->Unit) {
        assertTrue("Developer isolated Activity required",BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val id=UUID.randomUUID().toString();val parent=File(context.filesDir,"ui-tests");val root=File(parent,id)
        assertFalse(Files.isSymbolicLink(parent.toPath()));assertFalse(root.exists());assertFalse(Files.isSymbolicLink(root.toPath()))
        val scenario=ActivityScenario.launch<MainActivity>(Intent(context,MainActivity::class.java).putExtra("packrag.debug.uiTestId",id))
        try {
            lateinit var model:PackRagViewModel
            scenario.onActivity { model=ViewModelProvider(it)[PackRagViewModel::class.java] }
            compose.waitUntil(600_000){!model.state.value.busy}
            scenario.onActivity { activity -> activity.setContent {
                MaterialTheme { Column(Modifier.fillMaxSize().safeDrawingPadding()) {
                    // Fixed disclaimer remains visible even when the component body scrolls.
                    Text("UNSIGNED SYNTHETIC VALUES — COMPONENT TEST ONLY; no signed-pack admission",Modifier.padding(12.dp))
                    Column(Modifier.weight(1f).fillMaxWidth().verticalScroll(rememberScrollState()).padding(16.dp)){content()}
                } }
            } }
            compose.waitForIdle();foreground();assertions()
        } finally {
            scenario.close()
            val end=System.nanoTime()+10_000_000_000L;var released=false
            while(!released && System.nanoTime()<end) {
                released=runCatching { ProductSession(context,root,ProductConfiguration.keys(context),true).use { };true }.getOrDefault(false)
                if(!released)android.os.SystemClock.sleep(50)
            }
            kotlin.check(released);require(root.canonicalPath.startsWith(parent.canonicalPath+File.separator))
            assertFalse(Files.isSymbolicLink(root.toPath()))
            Files.walk(root.toPath()).use { paths -> require(paths.noneMatch { Files.isSymbolicLink(it) }) }
            assertTrue(root.deleteRecursively())
        }
    }
    private fun screenshot(name:String):JSONObject {
        compose.waitForIdle();foreground();android.os.SystemClock.sleep(750)
        var prior:String?=null;var equal=0;var last:Bitmap?=null;var hash=""
        try {
            repeat(3) {
                val image=requireNotNull(instrument.uiAutomation.takeScreenshot());val digest=MessageDigest.getInstance("SHA-256")
                for(y in 128 until image.height-160 step 24)for(x in 16 until image.width-16 step 24)
                    digest.update(ByteBuffer.allocate(4).putInt(image.getPixel(x,y)).array())
                hash=digest.digest().joinToString(""){"%02x".format(it)}
                equal=if(hash==prior)equal+1 else 1;prior=hash;last?.recycle();last=image
                if(it<2)android.os.SystemClock.sleep(250)
            }
            assertEquals(3,equal);foreground();val image=requireNotNull(last);val file=File(context.filesDir,name)
            file.outputStream().use { assertTrue(image.compress(Bitmap.CompressFormat.PNG,100,it)) }
            return JSONObject().put("sha256",Crypto.fileHash(file)).put("bytes",file.length()).put("width",image.width).put("height",image.height)
                .put("equal_static_frames",3).put("static_grid_sha256",hash).put("sample_interval_ms",250).put("minimum_wait_ms",750)
                .put("settling_only_system_margins_px",JSONArray(listOf(128,160)))
        } finally { last?.recycle() }
    }
    private fun record(name:String,cases:JSONArray,pngs:JSONObject,before:Map<String,String>) {
        assertEquals(before,LocalAssetImportTestSupport.ownerGuard())
        File(context.filesDir,name).writeText(JSONObject().put("status","PASS").put("cases",cases).put("visual_png",pngs)
            .put("values_sha256",valuesSha).put("authenticity_checked_in_this_component_method",false).put("actual_weight_inference",false)
            .put("owner_registry_and_model_sha256",JSONObject(before)).put("owner_guard_scope","EXPLICIT_50_PUBLIC_BASELINE_FILES_NO_ENUMERATION")
            .put("raw_reasoning_persisted",false).put("scope","Production presentation components hosted by setContent in existing isolated debug Activity using fixed unsigned synthetic owned values. Persistent disclaimer visible in every PNG. No new signed pack/publisher authentication, model generation, actual app navigation, largefont/narrow/global accessibility or fullF3/M4/product acceptance. Normal signed Activity/navigation and native smoke are independent methods.").toString(2),Charsets.UTF_8)
    }
    @Test fun longOwnedRowFieldsRemainLiteralAndReadableThroughIndependentScrolling() {
        val before=LocalAssetImportTestSupport.ownerGuard();val v=values();val item=row(v);val cases=JSONArray();val pngs=JSONObject()
        fun passed(id:String){cases.put(JSONObject().put("id",id).put("passed",true))}
        frame({InstalledPackOverview(item,v.getString("device_date"))}) {
            val name="Name: "+v.getString("name");val publisher="Publisher: "+v.getString("publisher_name")
            compose.onNodeWithText(name).performScrollTo().assertTextEquals(name).assertIsDisplayed()
            pngs.put("m4-pack-overview-long-name.png",screenshot("m4-pack-overview-long-name.png"))
            compose.onNodeWithText(publisher).performScrollTo().assertTextEquals(publisher).assertIsDisplayed()
            pngs.put("m4-pack-overview-long-publisher.png",screenshot("m4-pack-overview-long-publisher.png"))
            passed("literal-long-name-and-multilingual-publisher-text")
            for(line in listOf("Publisher public key ID: "+v.getString("publisher_key_id"),"Version: "+v.getString("version"),
                "Manifest SHA256: "+v.getString("manifest_sha256"),"Manifest bytes (signed JSON): 2586","Payload bytes (uncompressed): 85076","Transport bytes (KPack archive): 21565"))
                compose.onNodeWithText(line).performScrollTo().assertTextEquals(line).assertIsDisplayed()
            compose.onNodeWithText("Update check due: 2027-01-01",substring=true).performScrollTo().assertIsDisplayed()
            compose.onNodeWithText("Transport bytes (KPack archive): 21565").performScrollTo().assertIsDisplayed()
            pngs.put("m4-pack-overview-long-fields.png",screenshot("m4-pack-overview-long-fields.png"))
            passed("independently-scrolled-full-key-identity-date-and-byte-domains")
        }
        assertEquals(3,pngs.length());assertEquals(before,LocalAssetImportTestSupport.ownerGuard())
        passed("three-original-settled-row-pngs-and-known50-preservation");record("m4-pack-overview-long-row-ui.json",cases,pngs,before)
    }
    @Test fun longActiveChipKeepsClickRoleMinimumTargetAndFullIdentityCallback() {
        val before=LocalAssetImportTestSupport.ownerGuard();val v=values();val item=row(v)
        val older=item.copy(version=v.getString("older_version"),hash=v.getString("older_manifest_sha256"),active=false,overview=null)
        val cases=JSONArray();val pngs=JSONObject();var selected:PackIdentity?=null
        fun passed(id:String){cases.put(JSONObject().put("id",id).put("passed",true))}
        frame({ActivePackChips(listOf(older,item),false){selected=it}}) {
            val tag="active-pack-${item.tag}-${item.hash}";val node=compose.onNodeWithTag(tag).performScrollTo().assertIsDisplayed().assertHasClickAction()
            val semantics=node.fetchSemanticsNode();assertEquals(Role.Button,semantics.config[SemanticsProperties.Role])
            assertTrue(semantics.boundsInRoot.height>=48f*context.resources.displayMetrics.density)
            compose.onNodeWithText(item.tag+"\n"+v.getString("name")).assertTextEquals(item.tag+"\n"+v.getString("name")).assertIsDisplayed()
            passed("long-chip-click-role-and-minimum48dp-target")
            assertEquals(listOf(item.identity),activePackIdentities(listOf(older,item)));node.performClick()
            compose.runOnIdle { assertEquals(item.identity,selected);assertNotEquals(older.identity,selected) }
            passed("exact-full-identity-callback-and-inactive-old-version-exclusion")
            pngs.put("m4-pack-overview-long-chip.png",screenshot("m4-pack-overview-long-chip.png"))
        }
        assertEquals(1,pngs.length());assertEquals(before,LocalAssetImportTestSupport.ownerGuard())
        passed("original-settled-chip-png-and-known50-preservation");record("m4-pack-overview-long-chip-ui.json",cases,pngs,before)
    }
}
