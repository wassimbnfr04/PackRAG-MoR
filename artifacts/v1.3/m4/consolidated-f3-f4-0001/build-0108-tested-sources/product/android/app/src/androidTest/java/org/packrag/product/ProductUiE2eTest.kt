package org.packrag.product

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.v2.createEmptyComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextReplacement
import androidx.compose.ui.test.performScrollTo
import java.io.File
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Rule
import org.junit.Test
import org.junit.Assert.*
import org.junit.runner.RunWith
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.packrag.crypto.RawManifestVerifier as Crypto

/** Real GUI/native smoke; seeds only a fresh UUID registry, never the owner's default packs. */
@RunWith(AndroidJUnit4::class)
class ProductUiE2eTest {
    @get:Rule val compose=createEmptyComposeRule()

    @Test fun physicalUiQuestionToBufferedAnswerAndCanonicalSource() {
        val instrument=ProductUiTestSupport.instrument;val context=ProductUiTestSupport.context
        val before=LocalAssetImportTestSupport.ownerGuard()
        val canonical="The Aster-9 thermal controller has a maximum continuous operating temperature of 74 °C."
        ProductUiTestSupport.activity(prepare={ root ->
            assertFalse(root.exists());assertTrue(root.mkdirs())
            val input=File(root,"seed.kpack")
            try {
                instrument.context.assets.open("walking-skeleton.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
                assertEquals("19da286b9f0860c312dc8d14ce0ee8681bf12ca092a7b8a12171fd86abe02c7f",Crypto.fileHash(input))
                ProductSession(context,root,ProductConfiguration.keys(context),true).use { session ->
                    assertTrue(session.registry.snapshot().isEmpty())
                    session.registry.activate(input)
                    assertEquals("org.packrag.development.walking-skeleton",session.registry.snapshot().single().id)
                }
            } finally { assertTrue(input.delete()) }
        }) { scenario,model ->
            ProductUiTestSupport.ready(compose,model)
            assertEquals("Ready. Developer pack mode.",model.state.value.message)
            compose.onNodeWithText("Ready. Developer pack mode.").performScrollTo().assertIsDisplayed()
            compose.onNodeWithTag("query-question").performScrollTo().performTextReplacement("What is the maximum continuous operating temperature of the Aster-9?")
            compose.onNodeWithTag("query-date").performScrollTo().performTextReplacement("2026-10-05")
            ProductUiTestSupport.hideKeyboard(scenario)
            val previous=model.state.value
            compose.onNodeWithTag("query-submit").performScrollTo().performClick()
            compose.waitUntil(30_000) { model.state.value !== previous }
            compose.waitUntil(600_000) { !model.state.value.busy && model.state.value.completedResultId!=null }
            ProductUiTestSupport.ready(compose,model)
            val captured=model.state.value
            assertEquals("ANSWER_ACCEPTED",captured.answer?.state)
            assertTrue(requireNotNull(captured.answer?.text).contains("74 °C"))
            assertTrue(requireNotNull(captured.answer?.text).contains("[S1]"))
            assertFalse(requireNotNull(captured.answer?.text).contains("</think>"))
            val trace=requireNotNull(captured.trace);assertTrue(trace.emittedTokens in 1..512)
            val source=requireNotNull(captured.answer).sources.single()
            assertEquals(canonical,source.canonicalText)
            assertEquals(captured.installed.single().hash,source.pack.manifestSha256)
            compose.onNodeWithText("ANSWER_ACCEPTED").performScrollTo().assertIsDisplayed()
            compose.onNodeWithText("74 °C",substring=true).performScrollTo().assertIsDisplayed()
            compose.onNodeWithText("[S1] Aster-9 · G0-D01").performScrollTo().performClick()
            compose.onNodeWithTag("source-canonical-text").performScrollTo().assertTextEquals(canonical).assertIsDisplayed()
            compose.onNodeWithText("Pack identity: org.packrag.development.walking-skeleton@0.1.0").performScrollTo().assertIsDisplayed()
            compose.onNodeWithTag("source-back-answer").performScrollTo().performClick()
            compose.onNodeWithText("ANSWER_ACCEPTED").performScrollTo().assertIsDisplayed()
            assertSame(captured.answer,model.state.value.answer);assertEquals(captured.completedResultId,model.state.value.completedResultId)
            File(context.filesDir,"m4-isolated-ui-e2e.json").writeText(JSONObject().put("status","PASS")
                .put("cases",JSONArray(listOf("owned-authenticated-seed","real-gui-native-buffered-cited-answer","canonical-source-navigation-back-preserves-result").map { JSONObject().put("id",it).put("passed",true) }))
                .put("actual_weight_inference",true).put("answer",captured.answer!!.text).put("emitted_tokens",trace.emittedTokens)
                .put("canonical_source_sha256",source.canonicalTextSha256)
                .put("completed_result_id",captured.completedResultId).put("developer_pack_seeded_before_activity",true)
                .put("registry_scope","FRESH_CANONICAL_UUID_DEBUG_UI_TEST_ROOT_NOT_OWNER_DEFAULT")
                .put("raw_reasoning_persisted",false).put("owner_registry_and_model_sha256",JSONObject(before))
                .put("owner_guard_scope","EXPLICIT_50_PUBLIC_BASELINE_FILES_NO_ENUMERATION")
                .put("limits","One actual GUI/native English synthetic question and canonical source/back navigation; not real domain packs, calibrated gold, performance or full release acceptance").toString(2),Charsets.UTF_8)
        }
        assertEquals(before,LocalAssetImportTestSupport.ownerGuard())
    }
}
