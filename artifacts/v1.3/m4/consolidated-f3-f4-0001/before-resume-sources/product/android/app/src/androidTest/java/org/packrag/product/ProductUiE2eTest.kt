package org.packrag.product

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.v2.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.test.performScrollTo
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.lifecycle.ViewModelProvider
import java.io.File
import org.json.JSONObject
import org.junit.Rule
import org.junit.Test
import org.junit.Assert.assertEquals
import org.junit.rules.ExternalResource
import org.junit.rules.RuleChain
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ProductUiE2eTest {
    private val compose = createAndroidComposeRule<MainActivity>()
    private val preparedPack = object : ExternalResource() {
        override fun before() {
            val instrument = InstrumentationRegistry.getInstrumentation()
            val context = instrument.targetContext
            val key = instrument.context.assets.open("developer-public-key.raw").use { it.readBytes() }
            ProductSession(context, File(context.filesDir, "packs"), listOf(key), developerMode = true).use { session ->
                if (session.registry.snapshot().isEmpty()) {
                    val input = File(context.cacheDir, "m2-ui-seed.kpack")
                    try {
                        instrument.context.assets.open("walking-skeleton.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
                        session.registry.activate(input)
                    } finally { input.delete() }
                }
                require(session.registry.snapshot().size == 1 && session.registry.snapshot().single().id == "org.packrag.development.walking-skeleton")
            }
        }
    }
    @get:Rule val rules: RuleChain = RuleChain.outerRule(preparedPack).around(compose)

    @Test fun physicalUiQuestionToBufferedAnswerAndCanonicalSource() {
        compose.waitForIdle()
        lateinit var viewModel: PackRagViewModel
        compose.runOnUiThread { viewModel = ViewModelProvider(compose.activity)[PackRagViewModel::class.java] }
        compose.waitUntil(30_000) { !viewModel.state.value.busy }
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        File(context.filesDir, "m2-ui-phase.json").writeText(JSONObject().put("phase", "INITIAL_STATE")
            .put("message", viewModel.state.value.message).put("packs", viewModel.state.value.packs.joinToString(","))
            .toString(2), Charsets.UTF_8)
        assertEquals("Ready. Developer pack mode.", viewModel.state.value.message)
        compose.onNodeWithText("Ready. Developer pack mode.").assertIsDisplayed()
        compose.onNodeWithText("Question").performTextInput("What is the maximum continuous operating temperature of the Aster-9?")
        compose.onNodeWithText("Ask").performClick()
        compose.waitUntil(600_000) { compose.onAllNodesWithText("ANSWER_ACCEPTED").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("74 °C", substring = true).performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("[S1] Aster-9 · G0-D01").performScrollTo().performClick()
        compose.onNodeWithText("The Aster-9 thermal controller has a maximum continuous operating temperature of 74 °C.").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("org.packrag.development.walking-skeleton@0.1.0").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Back to answer").performScrollTo().performClick()
        compose.onNodeWithText("ANSWER_ACCEPTED").assertIsDisplayed()
        File(context.filesDir, "m2-ui-e2e.json").writeText(JSONObject().put("status", "PASS")
            .put("purpose", "PHYSICAL_INTERACTIVE_ANDROID_QUESTION_ANSWER_CANONICAL_SOURCE_SMOKE")
            .put("actual_weight_inference", true).put("developer_pack_seeded_before_activity", true)
            .put("canonical_source_navigation", true).put("buffered_final_answer", true)
            .put("limits", "One supported English synthetic question; not release packs, calibration, full screen/security/interactive performance acceptance").toString(2), Charsets.UTF_8)
    }
}
