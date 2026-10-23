package org.packrag.product

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.view.inputmethod.InputMethodManager
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.hasAnyAncestor
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.v2.createEmptyComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextReplacement
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.ext.junit.runners.AndroidJUnit4
import java.io.File
import java.nio.ByteBuffer
import java.security.MessageDigest
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto

/** Actual product Activity with its existing isolated debug-root contract; no setContent substitute. */
@RunWith(AndroidJUnit4::class)
class PackOverviewUiTest {
    @get:Rule val compose=createEmptyComposeRule()
    private val instrument get()=InstrumentationRegistry.getInstrumentation()
    private val context get()=instrument.targetContext
    private fun foreground(){assertEquals("org.packrag.product",instrument.uiAutomation.rootInActiveWindow?.packageName?.toString())}
    private fun click(tag:String){foreground();compose.onNodeWithTag(tag).performScrollTo().performClick()}
    private fun fingerprint(bitmap:Bitmap):String {
        val digest=MessageDigest.getInstance("SHA-256")
        for(y in 128 until bitmap.height-160 step 24)for(x in 16 until bitmap.width-16 step 24)
            digest.update(ByteBuffer.allocate(4).putInt(bitmap.getPixel(x,y)).array())
        return digest.digest().joinToString(""){"%02x".format(it)}
    }
    private fun screenshot(name:String):JSONObject {
        compose.waitForIdle();foreground();android.os.SystemClock.sleep(750)
        var prior:String?=null;var equal=0;var last:Bitmap?=null;var hash=""
        try {
            repeat(3) {
                val image=requireNotNull(instrument.uiAutomation.takeScreenshot());hash=fingerprint(image)
                equal=if(hash==prior)equal+1 else 1;prior=hash;last?.recycle();last=image
                if(it<2)android.os.SystemClock.sleep(250)
            }
            assertEquals("Viewport has not settled",3,equal);foreground()
            val image=requireNotNull(last);val file=File(context.filesDir,name)
            file.outputStream().use { assertTrue(image.compress(Bitmap.CompressFormat.PNG,100,it)) }
            return JSONObject().put("sha256",Crypto.fileHash(file)).put("bytes",file.length())
                .put("width",image.width).put("height",image.height).put("equal_static_frames",3)
                .put("static_grid_sha256",hash).put("sample_interval_ms",250).put("minimum_wait_ms",750)
                .put("settling_only_system_margins_px",JSONArray(listOf(128,160)))
        } finally { last?.recycle() }
    }
    @Test fun actualEmptySingleMultipleChipsAndVerifiedRowsNavigateByExactIdentity() {
        assertTrue(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val before=LocalAssetImportTestSupport.ownerGuard();val testId=UUID.randomUUID().toString()
        val root=File(context.filesDir,"ui-tests/$testId");val input=File(context.cacheDir,"overview-ui-$testId.kpack")
        val expectations=instrument.context.assets.open("pack-overview-corpus/expectations.json").bufferedReader().use { JSONObject(it.readText()).getJSONObject("fixtures") }
        val latest=expectations.getJSONObject("lifecycle-corpus/v2.kpack")
        val approved=expectations.getJSONObject("release-trust-corpus/calibration-schema-only.kpack")
        val cases=JSONArray();val pngs=JSONObject();var scenario:ActivityScenario<MainActivity>?=null;lateinit var model:PackRagViewModel
        fun passed(id:String){cases.put(JSONObject().put("id",id).put("passed",true))}
        fun ready(){compose.waitForIdle();compose.waitUntil(600_000){!model.state.value.busy};assertNotEquals("RUNTIME_ERROR",model.state.value.answer?.state);foreground()}
        fun tag(expect:JSONObject)=expect.getString("pack_id")+"@"+expect.getString("version")
        fun chip(expect:JSONObject)="active-pack-"+tag(expect)+"-"+expect.getString("manifest_sha256")
        try {
            ProductSession(context,root,ProductConfiguration.keys(context),true).use { session ->
                for(name in listOf("lifecycle-corpus/v1.kpack","lifecycle-corpus/v2.kpack","release-trust-corpus/calibration-schema-only.kpack")) {
                    instrument.context.assets.open(name).use { source->input.outputStream().use { source.copyTo(it) } }
                    assertEquals(expectations.getJSONObject(name).getString("transport_sha256"),Crypto.fileHash(input));session.registry.activate(input)
                }
                session.registry.snapshot().map { it.id }.forEach(session.registry::deactivate)
            }
            scenario=ActivityScenario.launch(Intent(context,MainActivity::class.java).putExtra("packrag.debug.uiTestId",testId).putExtra("packrag.debug.uiTestFontScale",2f).putExtra("packrag.debug.uiTestWidthDp",320))
            ProductUiTestSupport.awaitForeground(scenario!!)
            scenario!!.onActivity { model=ViewModelProvider(it)[PackRagViewModel::class.java] };ready()
            assertTrue(activePackIdentities(model.state.value.installed).isEmpty())
            compose.onNodeWithTag("active-packs-empty").performScrollTo().assertIsDisplayed();passed("empty-active-chips")
            click("manage-packs");compose.onNodeWithTag("pack-overview-"+tag(latest)).performScrollTo().assertIsDisplayed()
            val current=model.state.value.installed.single { it.id==latest.getString("pack_id") && it.version==latest.getString("version") }
            assertFalse(current.active);assertNotNull(current.overview)
            for(line in listOf("Publisher: PackRAG DEVELOPMENT ONLY","Publisher public key ID: "+latest.getString("publisher_key_id"),
                "Version: 1.0.1","Manifest bytes (signed JSON): 2589","Payload bytes (uncompressed): 85076","Transport bytes (KPack archive): 21562"))
                compose.onNode(hasText(line) and hasAnyAncestor(hasTestTag("pack-overview-"+tag(latest)))).performScrollTo().assertIsDisplayed()
            compose.onNode(hasText("Update check due: 2027-01-01",substring=true) and hasAnyAncestor(hasTestTag("pack-overview-"+tag(latest)))).performScrollTo().assertIsDisplayed()
            compose.onNodeWithTag("pack-overview-"+tag(latest)).performScrollTo().assertIsDisplayed()
            pngs.put("m4-pack-overview-installed.png",screenshot("m4-pack-overview-installed.png"))
            passed("verified-inactive-installed-row-fields")
            click("activate-"+tag(latest));ready();click("packs-back-answer")
            compose.onNodeWithTag(chip(latest)).performScrollTo().assertIsDisplayed();assertEquals(listOf(current.identity),activePackIdentities(model.state.value.installed))
            click(chip(latest));ready();assertEquals(current.identity,model.state.value.details!!.identity)
            assertEquals(current.identity,model.state.value.detailRequest);passed("one-active-chip-exact-current-version-manifest-navigation")
            click("details-back-packs");click("activate-"+tag(approved));ready();click("packs-back-answer")
            assertEquals(2,activePackIdentities(model.state.value.installed).size)
            compose.onNodeWithTag(chip(latest)).performScrollTo().assertIsDisplayed();compose.onNodeWithTag(chip(approved)).performScrollTo().assertIsDisplayed()
            passed("multiple-active-chips-distinct-identities")
            compose.onNodeWithTag("query-question").performScrollTo().performTextReplacement("What is the maximum continuous operating temperature of the Aster-9?")
            compose.onNodeWithTag("query-date").performScrollTo().performTextReplacement("2027-01-01")
            compose.onNodeWithTag("query-jurisdiction").performScrollTo().performTextReplacement("MA")
            val beforeSubmit=model.state.value.completedResultId
            click("query-submit")
            compose.waitUntil(10_000) { model.state.value.busy || model.state.value.completedResultId!=beforeSubmit };ready()
            val completed=model.state.value;assertEquals("NO_RELEVANT_EVIDENCE",completed.answer?.state)
            assertEquals(0,completed.trace!!.emittedTokens);assertFalse(completed.trace!!.diagnostics!!.generationCalled)
            assertNotEquals(beforeSubmit,completed.completedResultId);assertEquals("2027-01-01",completed.submission!!.query.asOf);assertEquals("MA",completed.submission!!.query.jurisdiction)
            scenario!!.onActivity { activity->
                (activity.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager).hideSoftInputFromWindow(activity.window.decorView.windowToken,0)
                activity.currentFocus?.clearFocus()
            };compose.waitForIdle()
            compose.onNodeWithTag("active-packs").performScrollTo().assertIsDisplayed()
            pngs.put("m4-pack-overview-active.png",screenshot("m4-pack-overview-active.png"))
            click(chip(approved));ready()
            assertEquals(approved.getString("manifest_sha256"),model.state.value.details!!.identity.manifestSha256)
            assertSame(completed.answer,model.state.value.answer);assertSame(completed.trace,model.state.value.trace)
            assertSame(completed.submission,model.state.value.submission);assertEquals(completed.completedResultId,model.state.value.completedResultId)
            passed("read-only-chip-details-preserve-completed-abstention-context")
            scenario!!.recreate();ProductUiTestSupport.awaitForeground(scenario!!);scenario!!.onActivity { model=ViewModelProvider(it)[PackRagViewModel::class.java] };ready()
            assertEquals(approved.getString("manifest_sha256"),model.state.value.detailRequest!!.manifestSha256)
            compose.onNodeWithTag("details-back-packs").performScrollTo().assertIsDisplayed();click("details-back-packs");click("packs-back-answer")
            assertEquals(2,activePackIdentities(model.state.value.installed).size);assertEquals(completed.completedResultId,model.state.value.completedResultId)
            passed("back-and-recreation-preserve-primitive-navigation")
            assertEquals(2,pngs.length());passed("exact-original-visible-viewport-screenshots")
            assertEquals(before,LocalAssetImportTestSupport.ownerGuard());passed("explicit-fifty-owner-public-files-unchanged")
            File(context.filesDir,"m4-pack-overview-ui.json").writeText(JSONObject().put("status","PASS").put("cases",cases).put("visual_png",pngs)
                .put("owner_registry_and_model_sha256",JSONObject(before)).put("owner_guard_scope","EXPLICIT_50_PUBLIC_BASELINE_FILES_NO_ENUMERATION")
                .put("completed_abstention_result_id",completed.completedResultId).put("raw_reasoning_persisted",false)
                .put("limits","Actual product Activity/chip/row/form submission/navigation/recreation. Fresh captured jurisdiction abstention0emitted tokens/no generation; model initialization is not excluded. PNGs unmodified, manual visible review mandatory. Real generation is separate background acceptance; no owner content/calibration, performance or fullF3/M4/release acceptance.").toString(2),Charsets.UTF_8)
        } finally {
            scenario?.close();input.delete()
            val end=System.nanoTime()+10_000_000_000L;var released=false
            while(!released && System.nanoTime()<end) {
                released=runCatching { ProductSession(context,root,ProductConfiguration.keys(context),true).use { };true }.getOrDefault(false)
                if(!released)android.os.SystemClock.sleep(50)
            }
            check(released);require(root.canonicalPath.startsWith(File(context.filesDir,"ui-tests").canonicalPath+File.separator))
            assertTrue(root.deleteRecursively())
        }
    }
}
