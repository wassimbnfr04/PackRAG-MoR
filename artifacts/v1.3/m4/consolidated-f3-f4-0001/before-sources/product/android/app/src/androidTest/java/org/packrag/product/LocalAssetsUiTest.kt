package org.packrag.product

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.view.KeyEvent
import android.view.WindowInsets
import android.view.inputmethod.InputMethodManager
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

/** Foreground real readiness and actual question-to-cited-answer path, isolated pack registry. */
@RunWith(AndroidJUnit4::class)
class LocalAssetsUiTest {
    @get:Rule val compose=createEmptyComposeRule()
    @Test fun realAssetCheckRecreationBackAndCitedAnswerKeepOwnedCompletion() {
        assertTrue(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext
        val id=UUID.randomUUID().toString();val root=File(context.filesDir,"ui-tests/$id")
        val cases=JSONArray();val screenshots=JSONObject();var scenario:ActivityScenario<MainActivity>?=null
        lateinit var model:PackRagViewModel
        fun guard():Map<String,String> = LocalAssetImportTestSupport.ownerGuard()
        val before=guard()
        fun settle(){compose.waitForIdle();compose.waitUntil(600_000){!model.state.value.busy};assertNotEquals("RUNTIME_ERROR",model.state.value.answer?.state)}
        fun click(tag:String,action:Boolean=false) {
            val prior=model.state.value;compose.onNodeWithTag(tag).performScrollTo().performClick()
            if(action) compose.waitUntil(30_000){model.state.value!==prior}
        }
        fun passed(name:String){cases.put(JSONObject().put("id",name).put("passed",true))}
        fun screenshot(name:String){
            val bitmap=requireNotNull(instrument.uiAutomation.takeScreenshot());val file=File(context.filesDir,name)
            try { file.outputStream().use { assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,it)) } } finally { bitmap.recycle() }
            screenshots.put(name,JSONObject().put("sha256",Crypto.fileHash(file)).put("bytes",file.length()))
        }
        fun hideIme(){
            scenario!!.onActivity { activity -> (activity.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager).hideSoftInputFromWindow(activity.window.decorView.windowToken,0) }
            compose.waitUntil(10_000){var hidden=false;scenario!!.onActivity { hidden=it.window.decorView.rootWindowInsets?.isVisible(WindowInsets.Type.ime())!=true };hidden}
        }
        try {
            val input=File(context.cacheDir,"asset-ui-$id.kpack")
            try {
                instrument.context.assets.open("walking-skeleton.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
                ProductSession(context,root,ProductConfiguration.keys(context),true).use { it.registry.activate(input) }
            } finally { input.delete() }
            scenario=ActivityScenario.launch(Intent(context,MainActivity::class.java).putExtra("packrag.debug.uiTestId",id))
            scenario!!.onActivity { model=ViewModelProvider(it)[PackRagViewModel::class.java] };settle()
            click("local-assets-open");compose.onNodeWithTag("local-assets-title").assertIsDisplayed()
            assertTrue(model.state.value.localAssets.all { it.condition==LocalAssetCondition.UNCHECKED })
            compose.onNodeWithTag("local-asset-GENERATOR").performScrollTo().assertTextContains("have not been checked",substring=true)
            click("local-assets-check",true);settle()
            assertEquals(4,model.state.value.localAssets.size);assertTrue(model.state.value.localAssets.all { it.condition==LocalAssetCondition.VERIFIED })
            assertNull(model.state.value.trace);assertNull(model.state.value.answer)
            val field=PackRagViewModel::class.java.getDeclaredField("session");field.isAccessible=true
            assertNull((field.get(model) as ProductSession).generatorLoadAndVerificationMs)
            passed("actual-four-file-check-before-query-initializes-neither-model")
            compose.onNodeWithTag("local-asset-GENERATOR").performScrollTo().assertTextContains("Exact size and SHA256",substring=true)
            screenshot("m4-local-assets-generator.png")
            scenario!!.recreate();scenario!!.onActivity { model=ViewModelProvider(it)[PackRagViewModel::class.java] };settle()
            compose.onNodeWithTag("local-assets-title").performScrollTo().assertIsDisplayed()
            compose.onNodeWithTag("local-asset-ENCODER").performScrollTo().assertTextContains("Exact size and SHA256",substring=true)
            screenshot("m4-local-assets-encoder.png")
            hideIme();instrument.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK);compose.waitForIdle()
            compose.onNodeWithTag("local-assets-title").assertDoesNotExist();passed("asset-page-recreates-and-system-back-returns-to-question")
            compose.onNodeWithTag("query-question").performScrollTo().performTextReplacement("What is the maximum continuous operating temperature of the Aster-9?")
            compose.onNodeWithTag("query-date").performScrollTo().performTextReplacement("2027-01-01")
            hideIme();click("query-submit",true);settle()
            val completed=model.state.value;assertEquals("ANSWER_ACCEPTED",completed.answer?.state)
            assertTrue(completed.answer!!.text!!.contains("74 °C"));assertTrue(completed.answer!!.text!!.contains("[S1]"));assertNotNull(completed.completedResultId)
            assertFalse(completed.answer!!.text!!.contains("</think>"));passed("actual-ui-question-retrieval-pinned-generation-and-validated-cited-answer")
            click("local-assets-open");click("local-assets-check",true);settle()
            assertSame(completed.answer,model.state.value.answer);assertSame(completed.trace,model.state.value.trace);assertSame(completed.submission,model.state.value.submission)
            assertEquals(completed.completedResultId,model.state.value.completedResultId)
            click("local-assets-back");compose.onNodeWithText("74 °C",substring=true).performScrollTo().assertIsDisplayed()
            passed("explicit-actual-file-check-and-page-return-preserve-owned-completed-answer")
            compose.onNodeWithText("[S1] Aster-9 · G0-D01").performScrollTo().performClick()
            compose.onNodeWithText("The Aster-9 thermal controller has a maximum continuous operating temperature of 74 °C.").performScrollTo().assertIsDisplayed()
            passed("canonical-evidence-navigation-remains-working-after-file-check")
            assertEquals(before,guard())
            File(context.filesDir,"m4-local-assets-ui.json").writeText(JSONObject().put("status","PASS").put("cases",cases).put("visual_png",screenshots)
                .put("actual_weight_inference",true).put("answer",completed.answer!!.text).put("completed_result_id",completed.completedResultId)
                .put("owner_registry_and_model_sha256",JSONObject(before)).put("owner_guard_scope","EXPLICIT_50_PUBLIC_BASELINE_FILES_NO_ENUMERATION").put("guards_unchanged",true).put("raw_reasoning_persisted",false)
                .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET").put("limits","Functional synthetic scope and tested viewport; PNGs require independent visual inspection; not domain expertise or performance benchmark.").toString(2),Charsets.UTF_8)
        } finally {
            scenario?.close();val end=System.nanoTime()+10_000_000_000L;var released=false
            while(!released && System.nanoTime()<end){released=runCatching { ProductSession(context,root,ProductConfiguration.keys(context),true).use { };true }.getOrDefault(false);if(!released) android.os.SystemClock.sleep(50)}
            check(released);require(root.canonicalPath.startsWith(File(context.filesDir,"ui-tests").canonicalPath+File.separator));root.deleteRecursively()
        }
    }
}
