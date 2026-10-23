package org.packrag.product

import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.v2.createEmptyComposeRule
import org.json.JSONObject
import org.junit.Assert.*
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.runner.RunWith
import org.junit.Rule
import org.junit.Test

@RunWith(AndroidJUnit4::class)
class ProductAccessibilityUiTest {
    @get:Rule val compose=createEmptyComposeRule()
    private val support get()=ProductUiTestSupport
    private fun click(tag:String){support.foreground();compose.onNodeWithTag(tag).performScrollTo().performClick()}
    @Test fun realNarrowLargeFontFormTouchTargetsStatusAndRecreationPreserveOwnedResult() {
        val before=LocalAssetImportTestSupport.ownerGuard();val images=JSONObject()
        val originalFont=support.context.resources.configuration.fontScale
        var actualWidth=0f;var buttonHeight=0f
        support.activity(ProductUiLayout(2f,320)) { scenario,model ->
            support.ready(compose,model);compose.onNodeWithTag("ui-test-layout").assertIsDisplayed()
            actualWidth=compose.onNodeWithTag("product-body").fetchSemanticsNode().boundsInRoot.width
            assertEquals(320f*support.context.resources.displayMetrics.density,actualWidth,2f)
            assertTrue(compose.onNodeWithText("PackRAG").fetchSemanticsNode().config.contains(SemanticsProperties.Heading))
            compose.onNodeWithTag("query-question").performScrollTo().performTextReplacement("Aster-9 test question")
            compose.onNodeWithTag("query-date").performScrollTo().performTextReplacement("2027-01-01")
            compose.onNodeWithTag("query-jurisdiction").performScrollTo().performTextReplacement("MA")
            support.hideKeyboard(scenario);compose.onNodeWithTag("query-submit").performScrollTo().assertHasClickAction()
            val button=compose.onNodeWithTag("query-submit").fetchSemanticsNode()
            assertEquals(Role.Button,button.config[SemanticsProperties.Role]);buttonHeight=button.boundsInRoot.height
            assertTrue(buttonHeight>=48f*support.context.resources.displayMetrics.density)
            images.put("m4-f3-large-font-form.png",support.screenshot(compose,"m4-f3-large-font-form.png"))
            click("query-submit");support.ready(compose,model);val completed=model.state.value
            assertEquals("NO_ACTIVE_PACK",completed.answer?.state);assertEquals(0,completed.trace!!.emittedTokens)
            assertEquals("2027-01-01",completed.submission!!.query.asOf);assertEquals("MA",completed.submission!!.query.jurisdiction)
            compose.onNodeWithTag("answer-guidance").performScrollTo().assertIsDisplayed()
            assertEquals(LiveRegionMode.Polite,compose.onNodeWithTag("answer-guidance").fetchSemanticsNode().config[SemanticsProperties.LiveRegion])
            images.put("m4-f3-large-font-abstention.png",support.screenshot(compose,"m4-f3-large-font-abstention.png"))
            scenario.recreate();support.awaitForeground(scenario);support.ready(compose,model)
            assertSame(completed.answer,model.state.value.answer);assertSame(completed.trace,model.state.value.trace)
            assertEquals(completed.completedResultId,model.state.value.completedResultId)
            compose.onNodeWithTag("query-question").performScrollTo().assertTextContains("Aster-9 test question")
            compose.onNodeWithTag("query-date").assertTextContains("2027-01-01")
            assertEquals(originalFont,support.context.resources.configuration.fontScale,0f)
        }
        support.record("m4-f3-accessibility-form.json",listOf("actual-main-activity-bounded320dp-two-times-compose-font",
            "actual-button-role-click-action-and-at-least48dp-rendered-bounds","fresh-gui-submitted-no-active-abstention-with-owned-date-jurisdiction",
            "polite-output-status-and-primitive-form-owned-result-recreation","phone-font-setting-and-fifty-owner-public-files-preserved"),before,images,
            JSONObject().put("observed_body_width_px",actualWidth).put("observed_button_height_px",buttonHeight).put("test_font_scale",2).put("test_viewport_dp",320)
                .put("global_font_scale_unchanged",true))
    }
    @Test fun largeFontAssetScreensExposeExpectedAndObservedEncoderBytesAndHashes() {
        val before=LocalAssetImportTestSupport.ownerGuard();val images=JSONObject()
        support.activity(ProductUiLayout(2f,320)) { scenario,model ->
            support.ready(compose,model);click("local-assets-open");click("local-assets-check");support.ready(compose,model)
            val status=model.state.value.localAssets.single { it.spec.slot==LocalAssetSlot.ENCODER }
            assertEquals(LocalAssetCondition.VERIFIED,status.condition)
            assertEquals(390004608L,status.observedBytes)
            assertEquals("68e592b160673d30250824c1116bc6ab33f70efb22b97c9e1d7ce1e69c1c9d70",status.observedSha256)
            compose.onNodeWithTag("local-asset-ENCODER-expected-size").performScrollTo().assertTextEquals("Expected size: 390004608 bytes")
            compose.onNodeWithTag("local-asset-ENCODER-observed-size").performScrollTo().assertTextEquals("Observed size: 390004608 bytes")
            images.put("m4-f3-large-font-encoder-size.png",support.screenshot(compose,"m4-f3-large-font-encoder-size.png"))
            compose.onNodeWithTag("local-asset-ENCODER-expected-hash").performScrollTo().assertTextEquals("Expected SHA256: 68e592b160673d30250824c1116bc6ab33f70efb22b97c9e1d7ce1e69c1c9d70")
            images.put("m4-f3-large-font-encoder-expected-hash.png",support.screenshot(compose,"m4-f3-large-font-encoder-expected-hash.png"))
            compose.onNodeWithTag("local-asset-ENCODER-observed-hash").performScrollTo().assertTextEquals("Observed SHA256: 68e592b160673d30250824c1116bc6ab33f70efb22b97c9e1d7ce1e69c1c9d70")
            images.put("m4-f3-large-font-encoder-observed-hash.png",support.screenshot(compose,"m4-f3-large-font-encoder-observed-hash.png"))
            scenario.recreate();support.awaitForeground(scenario);support.ready(compose,model)
            compose.onNodeWithTag("local-assets-title").performScrollTo().assertIsDisplayed();click("local-assets-back")
            compose.onNodeWithTag("diagnostics-toggle").performScrollTo().performClick()
            compose.onNodeWithTag("diagnostics-unavailable").performScrollTo().assertIsDisplayed()
        }
        support.record("m4-f3-accessibility-assets.json",listOf("actual-read-only-encoder-check-under-narrow-large-font-layout",
            "actual-independently-scrolled-expected-and-observed-encoder-byte-counts","actual-full-expected-and-observed-encoder-hash-fields",
            "primitive-assets-route-recreation-and-return-to-diagnostic-empty-state","fifty-owner-public-files-preserved"),before,images,
            JSONObject().put("test_font_scale",2).put("test_viewport_dp",320).put("encoder_fields_independently_scrolled",true))
    }
}
