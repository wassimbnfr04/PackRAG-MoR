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

/** Focused real Activity check on a fresh emulator; no fabricated phone baseline. */
@RunWith(AndroidJUnit4::class)
class EmulatorUiSmokeTest {
    @get:Rule val compose=createEmptyComposeRule()
    @Test fun normalFontAndRepairedLargeFontFormSubmitRealNoPackAbstention() {
        val support=ProductUiTestSupport
        assertTrue(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val qemu=support.instrument.uiAutomation.executeShellCommand("getprop ro.kernel.qemu")
        val observed=android.os.ParcelFileDescriptor.AutoCloseInputStream(qemu).bufferedReader().use{it.readText().trim()}
        assertEquals("1",observed)
        val ownerNames=listOf("models","packs","production-registry")
        ownerNames.forEach{assertFalse("Fresh emulator must have no owner root: $it",File(support.context.filesDir,it).exists())}
        assertEquals(1f,support.context.resources.configuration.fontScale,0f)
        val images=JSONObject()
        support.activity { scenario,model ->
            support.ready(compose,model)
            compose.onNodeWithTag("ui-test-layout").assertDoesNotExist()
            compose.onNodeWithTag("query-date").performScrollTo().assertIsDisplayed()
            support.hideKeyboard(scenario)
            images.put("m4-emulator-normal-form.png",support.screenshot(compose,"m4-emulator-normal-form.png"))
        }
        support.activity(ProductUiLayout(2f,320)) { scenario,model ->
            support.ready(compose,model)
            compose.onNodeWithTag("query-question").performScrollTo().performTextReplacement("Aster-9 test question")
            compose.onNodeWithTag("query-date").performScrollTo().performTextReplacement("2027-01-01")
            support.hideKeyboard(scenario)
            compose.onNodeWithTag("query-date").performScrollTo().assertIsDisplayed()
            images.put("m4-emulator-large-font-date.png",support.screenshot(compose,"m4-emulator-large-font-date.png"))
            compose.onNodeWithTag("query-jurisdiction").performScrollTo().performTextReplacement("MA")
            support.hideKeyboard(scenario)
            compose.onNodeWithTag("query-submit").performScrollTo().assertIsDisplayed()
            images.put("m4-emulator-large-font-submit.png",support.screenshot(compose,"m4-emulator-large-font-submit.png"))
            compose.onNodeWithTag("query-submit").performClick()
            support.ready(compose,model)
            val completed=model.state.value
            assertEquals("NO_ACTIVE_PACK",completed.answer!!.state)
            assertEquals(0,completed.trace!!.emittedTokens)
            assertEquals("2027-01-01",completed.submission!!.query.asOf)
            assertEquals("MA",completed.submission!!.query.jurisdiction)
            compose.onNodeWithTag("answer-guidance").performScrollTo().assertIsDisplayed()
            images.put("m4-emulator-no-pack-abstention.png",support.screenshot(compose,"m4-emulator-no-pack-abstention.png"))
            scenario.recreate();support.awaitForeground(scenario);support.ready(compose,model)
            assertEquals(completed.completedResultId,model.state.value.completedResultId)
            assertSame(completed.answer,model.state.value.answer)
        }
        ownerNames.forEach{assertFalse(File(support.context.filesDir,it).exists())}
        assertEquals(1f,support.context.resources.configuration.fontScale,0f)
        File(support.context.filesDir,"m4-emulator-ui-smoke.json").writeText(JSONObject()
            .put("status","PASS").put("emulator_qemu",observed).put("actual_weight_inference",false)
            .put("global_font_scale",1).put("raw_reasoning_persisted",false)
            .put("cases",JSONArray(listOf("normal-layout-without-resource-override","scoped-two-times-date-and-jurisdiction-form",
                "actual-no-active-pack-zero-generation-context-preserved","recreation-owned-result-and-clean-emulator-owner-roots-preserved")))
            .put("visual_png",images)
            .put("scope","Real isolated MainActivity on fresh emulator. Original PNG review required. No physical-phone performance/native-inference or full M4 acceptance claim.")
            .toString(2),Charsets.UTF_8)
    }
}
