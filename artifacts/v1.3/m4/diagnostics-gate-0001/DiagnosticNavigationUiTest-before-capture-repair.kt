package org.packrag.product

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.view.KeyEvent
import android.view.WindowInsets
import android.view.inputmethod.InputMethodManager
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.v2.createEmptyComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto

/** Actual foreground/Back/recreation, with original diagnostic and canonical PNGs. */
@RunWith(AndroidJUnit4::class)
class DiagnosticNavigationUiTest {
    @get:Rule val compose=createEmptyComposeRule()
    @Test fun accessibleCheckboxCapturedDiagnosticsSourceAndManagementRestoreAndNavigateLocally() {
        assertTrue(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext
        val testId=UUID.randomUUID().toString();val root=File(context.filesDir,"ui-tests/$testId")
        fun guard():Map<String,String> = listOf("packs","production-registry","models").flatMap { name ->
            val folder=File(context.filesDir,name);if(!folder.exists()) emptyList() else folder.walkTopDown().filter { it.isFile }
                .map { it.relativeTo(context.filesDir).path to Crypto.fileHash(it) }.toList()
        }.toMap()
        val before=guard();val cases=JSONArray();val screenshots=JSONObject();var scenario:ActivityScenario<MainActivity>?=null
        lateinit var model:PackRagViewModel
        fun ready() { compose.waitUntil(600_000) { !model.state.value.busy };assertNotEquals("RUNTIME_ERROR",model.state.value.answer?.state) }
        fun click(tag:String) { compose.onNodeWithTag(tag).performScrollTo().performClick() }
        fun replace(tag:String,value:String) { compose.onNodeWithTag(tag).performScrollTo().performTextReplacement(value) }
        fun passed(id:String) { cases.put(JSONObject().put("id",id).put("passed",true)) }
        fun screenshot(name:String) {
            val bitmap=requireNotNull(instrument.uiAutomation.takeScreenshot());val file=File(context.filesDir,name)
            try { file.outputStream().use { assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,it)) } }
            finally { bitmap.recycle() }
            screenshots.put(name,JSONObject().put("sha256",Crypto.fileHash(file)).put("bytes",file.length()))
        }
        fun back() {
            scenario!!.onActivity { activity -> (activity.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager)
                .hideSoftInputFromWindow(activity.window.decorView.windowToken,0) }
            compose.waitUntil(10_000) {
                var hidden=false
                scenario!!.onActivity { hidden=it.window.decorView.rootWindowInsets?.isVisible(WindowInsets.Type.ime())!=true }
                hidden
            }
            instrument.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK);compose.waitForIdle()
        }
        try {
            val input=File(context.cacheDir,"diagnostic-navigation-$testId.kpack")
            try {
                instrument.context.assets.open("walking-skeleton.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
                assertEquals("19da286b9f0860c312dc8d14ce0ee8681bf12ca092a7b8a12171fd86abe02c7f",Crypto.fileHash(input))
                ProductSession(context,root,ProductConfiguration.keys(context),true).use { it.registry.activate(input) }
            } finally { input.delete() }
            scenario=ActivityScenario.launch(Intent(context,MainActivity::class.java).putExtra("packrag.debug.uiTestId",testId))
            scenario!!.onActivity { model=ViewModelProvider(it)[PackRagViewModel::class.java] };ready()
            val checkbox=compose.onNodeWithTag("query-current-law")
            checkbox.performScrollTo().assert(SemanticsMatcher.expectValue(SemanticsProperties.Role,Role.Checkbox))
                .assertTextContains("Current law only (exclude repealed/superseded)").assertIsOff()
            compose.onAllNodes(SemanticsMatcher.expectValue(SemanticsProperties.Role,Role.Checkbox),useUnmergedTree=true).assertCountEquals(1)
            compose.onNodeWithText("Current law only (exclude repealed/superseded)").performScrollTo().performClick()
            checkbox.assertIsOn();passed("one-labelled-checkbox-role-and-state-label-click-toggles-once")
            click("diagnostics-toggle");compose.onNodeWithTag("diagnostics-unavailable").performScrollTo().assertIsDisplayed()
            val question="What is the maximum continuous operating temperature of the Aster-9?"
            replace("query-question",question);replace("query-date","2027-01-01");click("query-submit")
            compose.waitUntil(10_000) { model.state.value.busy }
            assertNull(model.state.value.trace);assertNull(model.state.value.answer);assertNull(model.state.value.completedResultId)
            ready()
            val captured=model.state.value;val trace=requireNotNull(captured.trace);val resultId=requireNotNull(captured.completedResultId)
            assertEquals("ANSWER_ACCEPTED",trace.answer.state);assertTrue(trace.answer.text!!.contains("74 °C"))
            assertTrue(trace.diagnostics!!.generationCalled);assertTrue(captured.submission!!.query.currentLaw)
            compose.onNodeWithTag("completed-diagnostics").performScrollTo().assertIsDisplayed()
            screenshot("m4-diagnostic-home.png");passed("actual-buffered-cited-answer-has-completed-only-diagnostics")
            replace("query-question","Edited form remains separate");replace("query-date","2028-02-29");replace("query-jurisdiction","MA")
            scenario!!.recreate();scenario!!.onActivity { model=ViewModelProvider(it)[PackRagViewModel::class.java] }
            assertSame(trace,model.state.value.trace);assertEquals(resultId,model.state.value.completedResultId)
            compose.onNodeWithTag("query-date").performScrollTo().assertTextContains("2028-02-29")
            compose.onNodeWithTag("query-question").performScrollTo().assertTextContains("Edited form remains separate")
            compose.onNodeWithTag("completed-diagnostics").performScrollTo().assertIsDisplayed()
            compose.onNodeWithText("Captured question: $question").performScrollTo().assertIsDisplayed()
            passed("form-toggle-and-original-diagnostic-context-survive-activity-recreation")
            val source=trace.answer.sources.single()
            compose.onNodeWithText("[S1] Aster-9 · G0-D01").performScrollTo().performClick()
            scenario!!.recreate();scenario!!.onActivity { model=ViewModelProvider(it)[PackRagViewModel::class.java] }
            compose.onNodeWithTag("source-canonical-text").performScrollTo().assertTextEquals(source.canonicalText).assertIsDisplayed()
            screenshot("m4-diagnostic-source.png");assertSame(trace,model.state.value.trace)
            back();compose.onNodeWithTag("diagnostics-toggle").performScrollTo().assertTextContains("Hide diagnostics")
            assertSame(trace,model.state.value.trace);assertEquals(resultId,model.state.value.completedResultId)
            passed("saved-source-identifiers-bind-same-result-and-real-back-returns-to-answer")
            click("manage-packs");val pack=captured.installed.single();click("details-${pack.tag}");ready()
            assertNotNull(model.state.value.details);assertSame(trace,model.state.value.trace)
            scenario!!.recreate();scenario!!.onActivity { model=ViewModelProvider(it)[PackRagViewModel::class.java] }
            compose.onNodeWithTag("details-back-packs").performScrollTo().assertIsDisplayed()
            back();compose.onNodeWithText("Installed packs").performScrollTo().assertIsDisplayed();assertNull(model.state.value.detailRequest)
            back();compose.onNodeWithTag("diagnostics-toggle").performScrollTo().assertTextContains("Hide diagnostics")
            assertSame(trace,model.state.value.trace);assertEquals(resultId,model.state.value.completedResultId)
            passed("management-and-verified-details-restore-with-back-details-list-answer")
            compose.onNodeWithText("[S1] Aster-9 · G0-D01").performScrollTo().performClick()
            instrument.runOnMainSync { model.cancel() }
            compose.onNodeWithTag("diagnostics-unavailable").performScrollTo().assertIsDisplayed()
            compose.onNodeWithTag("source-canonical-text").assertDoesNotExist()
            scenario!!.recreate();scenario!!.onActivity { model=ViewModelProvider(it)[PackRagViewModel::class.java] }
            assertNull(model.state.value.completedResultId);assertNull(model.state.value.trace)
            compose.onNodeWithTag("source-canonical-text").assertDoesNotExist()
            compose.onNodeWithTag("diagnostics-unavailable").performScrollTo().assertIsDisplayed()
            passed("cancel-clears-source-binding-and-recreation-cannot-restore-stale-source")
            assertEquals(before,guard());passed("owner-default-registries-models-and-payloads-byte-identical-within-run")
            File(context.filesDir,"m4-diagnostic-navigation.json").writeText(JSONObject().put("status","PASS").put("cases",cases)
                .put("visual_png",screenshots).put("actual_weight_inference",true).put("answer",trace.answer.text)
                .put("captured_query",trace.diagnostics!!.context.query.raw).put("manifest_sha256",source.pack.manifestSha256)
                .put("canonical_text",source.canonicalText).put("canonical_sha256",source.canonicalTextSha256)
                .put("owner_registry_and_model_sha256",JSONObject(before)).put("raw_reasoning_persisted",false)
                .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET")
                .put("limits","Actual Activity recreation and injected Android Back keys on owner configuration; not process kill, all viewports, real calibration/content, semantic entailment or performance acceptance. PNGs require independent visual inspection.").toString(2),Charsets.UTF_8)
        } finally {
            scenario?.close();val end=System.nanoTime()+10_000_000_000L;var released=false
            while(!released && System.nanoTime()<end) {
                released=runCatching { ProductSession(context,root,ProductConfiguration.keys(context),true).use { };true }.getOrDefault(false)
                if(!released) android.os.SystemClock.sleep(50)
            }
            check(released);require(root.canonicalPath.startsWith(File(context.filesDir,"ui-tests").canonicalPath+File.separator));root.deleteRecursively()
        }
    }
}
