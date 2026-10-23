package org.packrag.product

import android.content.Intent
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertTextContains
import androidx.compose.ui.test.junit4.v2.createEmptyComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextReplacement
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

/** Foreground actual-model test; form edits/recreation must not relabel submitted evidence. */
@RunWith(AndroidJUnit4::class)
class QueryControlsUiTest {
    @get:Rule val compose = createEmptyComposeRule()
    @Test fun capturedControlsSurviveRealGenerationEditsRecreationAndSourceNavigation() {
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext
        val testId=UUID.randomUUID().toString();val root=File(context.filesDir,"ui-tests/$testId")
        fun guardedFiles():Map<String,String> = LocalAssetImportTestSupport.ownerGuard()
        val before=guardedFiles();val cases=JSONArray();var scenario:ActivityScenario<MainActivity>?=null
        lateinit var model:PackRagViewModel
        fun settle() { compose.waitForIdle();compose.waitUntil(600_000) { !model.state.value.busy };assertNotEquals("RUNTIME_ERROR",model.state.value.answer?.state) }
        fun replace(tag:String,value:String) { compose.onNodeWithTag(tag).performScrollTo().performTextReplacement(value) }
        fun click(tag:String) {
            val previous=model.state.value
            compose.onNodeWithTag(tag).performScrollTo().performClick()
            // Checkbox changes only local form state; submit changes ViewModel state synchronously when dispatched.
            if(tag=="query-submit") compose.waitUntil(30_000) { model.state.value !== previous }
        }
        fun passed(id:String) { cases.put(JSONObject().put("id",id).put("passed",true)) }
        try {
            val input=File(context.cacheDir,"query-ui-$testId.kpack")
            try {
                instrument.context.assets.open("walking-skeleton.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
                ProductSession(context,root,ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS).use { it.registry.activate(input) }
            } finally { input.delete() }
            scenario=ActivityScenario.launch(Intent(context,MainActivity::class.java).putExtra("packrag.debug.uiTestId",testId).putExtra("packrag.debug.uiTestFontScale",2f).putExtra("packrag.debug.uiTestWidthDp",320))
            ProductUiTestSupport.awaitForeground(scenario!!)
            scenario!!.onActivity { model=ViewModelProvider(it)[PackRagViewModel::class.java] };settle()
            compose.onNodeWithTag("local-processing").assertIsDisplayed()
            val question="What is the maximum continuous operating temperature of the Aster-9?"
            replace("query-question",question);replace("query-date","2027-02-29");click("query-submit");settle()
            assertEquals("INVALID_QUERY",model.state.value.answer?.state);assertNull(model.state.value.trace)
            compose.onNodeWithTag("query-input-error").performScrollTo().assertTextContains("INVALID_QUERY_DATE",substring=true)
            passed("invalid-date-visible-actionable-error-no-trace")
            replace("query-date","2027-01-01");click("query-current-law");click("query-submit")
            compose.waitUntil(10_000) { model.state.value.busy }
            assertEquals("2027-01-01",model.state.value.submission?.query?.asOf)
            assertNull(model.state.value.answer);assertNull(model.state.value.trace)
            replace("query-date","2028-02-29");replace("query-jurisdiction","MA-01");replace("query-question","Edited form question")
            assertTrue("Form edits must occur during actual generation",model.state.value.busy)
            scenario!!.recreate();ProductUiTestSupport.awaitForeground(scenario!!);scenario!!.onActivity { model=ViewModelProvider(it)[PackRagViewModel::class.java] }
            compose.onNodeWithTag("query-date").performScrollTo().assertTextContains("2028-02-29")
            compose.onNodeWithTag("query-jurisdiction").performScrollTo().assertTextContains("MA-01")
            compose.onNodeWithTag("query-question").performScrollTo().assertTextContains("Edited form question")
            settle()
            val trace=requireNotNull(model.state.value.trace);val captured=requireNotNull(model.state.value.submission)
            assertEquals("ANSWER_ACCEPTED",trace.answer.state);assertEquals(question,captured.query.raw)
            assertEquals("2027-01-01",captured.query.asOf);assertNull(captured.query.jurisdiction);assertTrue(captured.query.currentLaw)
            assertEquals(captured.query,trace.evidenceContext?.query)
            compose.onNodeWithTag("submitted-query-context").performScrollTo().assertTextContains("As-of: 2027-01-01 · Jurisdiction: all · Current law only: true")
            compose.onNodeWithTag("submitted-freshness").performScrollTo().assertTextContains("submitted date 2027-01-01",substring=true)
            compose.onNodeWithText("74 °C",substring=true).performScrollTo().assertIsDisplayed()
            passed("actual-stale-cited-answer-retains-submitted-controls-across-edits-and-recreation")
            compose.onNodeWithText("[S1] Aster-9 · G0-D01").performScrollTo().performClick()
            compose.onNodeWithText("The Aster-9 thermal controller has a maximum continuous operating temperature of 74 °C.").performScrollTo().assertIsDisplayed()
            compose.onNodeWithText("Back to answer").performScrollTo().performClick()
            passed("retained-actual-canonical-source-navigation")
            replace("query-question",question)
            compose.onNodeWithTag("query-date").performScrollTo().assertTextContains("2028-02-29")
            compose.onNodeWithTag("query-jurisdiction").performScrollTo().assertTextContains("MA-01")
            val previousCompletion=requireNotNull(model.state.value.completedResultId)
            click("query-submit")
            val immediate=model.state.value
            val resubmission=JSONObject().put("previous_completion_id",previousCompletion)
                .put("immediate_busy",immediate.busy).put("immediate_completion_id",immediate.completedResultId ?: JSONObject.NULL)
                .put("immediate_answer_state",immediate.answer?.state ?: JSONObject.NULL)
                .put("immediate_submitted_date",immediate.submission?.query?.asOf ?: JSONObject.NULL)
                .put("immediate_submitted_jurisdiction",immediate.submission?.query?.jurisdiction ?: JSONObject.NULL)
            val observation=File(context.filesDir,"m4-ui-query-resubmission-observation.json")
            observation.writeText(resubmission.put("status","OBSERVED_BEFORE_COMPLETION_WAIT_NOT_PASS").toString(2),Charsets.UTF_8)
            // A posted UI tap can leave the prior non-busy result visible briefly.
            // Wait for this submitted context AND a distinct completed result; a fast abstention need not expose busy.
            compose.waitUntil(600_000) {
                val value=model.state.value
                !value.busy && value.completedResultId!=null && value.completedResultId!=previousCompletion &&
                    value.submission?.query?.raw==question && value.submission?.query?.asOf=="2028-02-29" &&
                    value.submission?.query?.jurisdiction=="MA-01"
            }
            settle()
            assertNotEquals(previousCompletion,model.state.value.completedResultId)
            resubmission.put("status","NEW_COMPLETION_OBSERVED_ASSERTIONS_PENDING")
                .put("new_completion_id",model.state.value.completedResultId)
                .put("new_answer_state",model.state.value.answer?.state)
            observation.writeText(resubmission.toString(2),Charsets.UTF_8)
            assertEquals("NO_RELEVANT_EVIDENCE",model.state.value.answer?.state)
            assertEquals("2028-02-29",model.state.value.submission?.query?.asOf);assertEquals("MA-01",model.state.value.submission?.query?.jurisdiction)
            compose.onNodeWithTag("answer-guidance").performScrollTo().assertTextContains("date/jurisdiction",substring=true)
            assertNull(model.state.value.answer?.text);assertEquals(0,model.state.value.trace?.emittedTokens)
            passed("later-submit-uses-edited-controls-and-replaces-old-answer")
            observation.writeText(resubmission.put("status","PASS_NEW_COMPLETION_EDITED_CONTEXT_ABSTENTION").toString(2),Charsets.UTF_8)
            assertEquals(before,guardedFiles());passed("explicit-fifty-owner-public-files-unchanged")
            File(context.filesDir,"m4-ui-query-controls.json").writeText(JSONObject().put("status","PASS").put("cases",cases)
                .put("actual_weight_inference",true).put("question",captured.query.raw).put("as_of",captured.query.asOf)
                .put("current_law",captured.query.currentLaw).put("answer",trace.answer.text).put("prefill_tokens",trace.prefillTokens)
                .put("evidence_tokens",trace.evidenceTokens).put("emitted_tokens",trace.emittedTokens)
                .put("session_wall_ms_including_lazy_initialization",trace.totalMs).put("initialization_ms",trace.initializationMs)
                .put("owner_registry_and_model_sha256",JSONObject(before)).put("owner_guard_scope","EXPLICIT_50_PUBLIC_BASELINE_FILES_NO_ENUMERATION").put("raw_reasoning_persisted",false)
                .put("limits","One synthetic English supported question, real UI edits and Activity recreation; not process-death/benchmark/final legal pack acceptance.")
                .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET").toString(2),Charsets.UTF_8)
        } finally {
            scenario?.close();val end=System.nanoTime()+10_000_000_000L;var released=false
            while(!released && System.nanoTime()<end) {
                released=runCatching { ProductSession(context,root,ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS).use { };true }.getOrDefault(false)
                if(!released) android.os.SystemClock.sleep(50)
            }
            check(released);require(root.canonicalPath.startsWith(File(context.filesDir,"ui-tests").canonicalPath+File.separator));root.deleteRecursively()
        }
    }
}
