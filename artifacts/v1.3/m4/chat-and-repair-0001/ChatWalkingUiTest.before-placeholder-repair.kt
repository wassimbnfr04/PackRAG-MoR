package org.packrag.product

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

/** Real chat shell/ViewModel path; missing pack is an honest zero-generation control. */
@RunWith(AndroidJUnit4::class)
class ChatWalkingUiTest {
    @get:Rule val compose=createEmptyComposeRule()
    @Test fun realChatComposerTwoOwnedTurnsMenuNewChatAndRecreation() {
        val support=ProductUiTestSupport
        val images=JSONObject()
        val qemu=support.instrument.uiAutomation.executeShellCommand("getprop ro.kernel.qemu")
        assertEquals("1",android.os.ParcelFileDescriptor.AutoCloseInputStream(qemu).bufferedReader().use{it.readText().trim()})
        val owners=listOf("packs","production-registry","models")
        owners.forEach{assertFalse(File(support.context.filesDir,it).exists())}
        support.activity { scenario,model ->
            support.ready(compose,model)
            compose.onNodeWithTag("chat-composer").assertIsDisplayed()
            compose.onNodeWithTag("query-submit").assertIsNotEnabled()
            images.put("m4-chat-normal-empty.png",support.screenshot(compose,"m4-chat-normal-empty.png"))
            compose.onNodeWithTag("query-question").performTextReplacement("How do I repair a bicycle inner tube?")
            support.hideKeyboard(scenario)
            compose.onNodeWithTag("query-controls-toggle").performClick()
            compose.onNodeWithTag("query-date").performScrollTo().performTextReplacement("2027-01-01")
            compose.onNodeWithTag("query-jurisdiction").performScrollTo().performTextReplacement("MA")
            support.hideKeyboard(scenario)
            compose.onNodeWithTag("query-controls-toggle").performScrollTo().performClick()
            compose.onNodeWithTag("query-submit").performClick()
            compose.waitUntil(20_000){model.turns.value.size==1 && !model.state.value.busy}
            val first=model.turns.value.single()
            assertEquals("NO_ACTIVE_PACK",first.answer.state)
            assertEquals(0,model.state.value.trace!!.emittedTokens)
            assertEquals("2027-01-01",first.submission.query.asOf)
            assertEquals("MA",first.submission.query.jurisdiction)
            compose.onNodeWithTag("query-question").assertTextEquals("")
            compose.onNodeWithTag("query-question").performTextReplacement("How do I clean the fan in a Framework Laptop 12?")
            support.hideKeyboard(scenario)
            compose.onNodeWithTag("query-submit").performClick()
            compose.waitUntil(20_000){model.turns.value.size==2 && !model.state.value.busy}
            assertNotEquals(first.resultId,model.turns.value.last().resultId)
            assertEquals(first.resultId,model.turns.value.first().resultId)
            compose.onNodeWithTag("assistant-"+model.turns.value.last().resultId).performScrollTo().assertIsDisplayed()
            images.put("m4-chat-two-turns.png",support.screenshot(compose,"m4-chat-two-turns.png"))
            scenario.recreate();support.awaitForeground(scenario);support.ready(compose,model)
            assertEquals(2,model.turns.value.size)
            compose.onNodeWithTag("app-menu").performClick()
            compose.onNodeWithTag("local-assets-open").performScrollTo().performClick()
            compose.onNodeWithTag("local-assets-title").performScrollTo().assertIsDisplayed()
            compose.onNodeWithTag("local-assets-back").performScrollTo().performClick()
            compose.onNodeWithTag("new-chat").performClick()
            assertTrue(model.turns.value.isEmpty());assertNull(model.state.value.completedResultId)
            compose.onNodeWithTag("query-submit").assertIsNotEnabled()
        }
        support.activity(ProductUiLayout(2f,320)) { scenario,model ->
            support.ready(compose,model)
            compose.onNodeWithTag("query-question").performTextReplacement("Describe a repair procedure for my device.")
            support.hideKeyboard(scenario)
            images.put("m4-chat-large-font-composer.png",support.screenshot(compose,"m4-chat-large-font-composer.png"))
            compose.onNodeWithTag("query-controls-toggle").performClick()
            compose.onNodeWithTag("query-date").performScrollTo().assertIsDisplayed()
            support.hideKeyboard(scenario)
            images.put("m4-chat-large-font-controls.png",support.screenshot(compose,"m4-chat-large-font-controls.png"))
        }
        owners.forEach{assertFalse(File(support.context.filesDir,it).exists())}
        File(support.context.filesDir,"m4-chat-walking.json").writeText(JSONObject().put("status","PASS")
            .put("actual_weight_inference",false).put("raw_reasoning_persisted",false).put("environment","FRESH_EMULATOR")
            .put("cases",JSONArray(listOf("real-normal-chat-shell-and-disabled-empty-submit","two-distinct-owned-no-pack-turns-with-captured-controls",
                "recreation-menu-local-assets-return-and-new-chat","real-scoped-large-font-composer-and-query-controls")))
            .put("visual_png",images).put("scope","Actual isolated MainActivity and real ViewModel no-pack path. Four original PNGs require review. Does not establish repair capability or phone native performance; real repair inference is a separate gate.").toString(2),Charsets.UTF_8)
    }
}
