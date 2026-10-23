package org.packrag.product

import android.content.Intent
import android.graphics.Bitmap
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertTextContains
import androidx.compose.ui.test.assertTextEquals
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
import org.packrag.model.*
import org.packrag.packs.*
import org.packrag.retrieval.Candidate
import org.packrag.sources.SourceScreen

/** Real product English flow plus clearly separate signed AR/FR viewer-component controls. */
@RunWith(AndroidJUnit4::class)
class SourceDetailsUiTest {
    @get:Rule val compose=createEmptyComposeRule()
    private val instrument get()=InstrumentationRegistry.getInstrumentation()
    private val context get()=instrument.targetContext
    private fun guard():Map<String,String> = LocalAssetImportTestSupport.ownerGuard()
    private fun cleanup(root:File) {
        val end=System.nanoTime()+10_000_000_000L;var released=false
        while(!released && System.nanoTime()<end) {
            released=runCatching { ProductSession(context,root,ProductConfiguration.keys(context),true).use { };true }.getOrDefault(false)
            if(!released) android.os.SystemClock.sleep(50)
        }
        check(released);require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));assertTrue(root.deleteRecursively())
    }
    @Test fun realAnswerCanonicalDetailsActiveInactiveAndSharedMutationControls() {
        assertTrue(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val id=UUID.randomUUID().toString();val root=File(context.filesDir,"ui-tests/$id");val before=guard();val cases=JSONArray()
        var scenario:ActivityScenario<MainActivity>?=null;lateinit var model:PackRagViewModel
        fun settle() { compose.waitForIdle();compose.waitUntil(600_000) { !model.state.value.busy };assertNotEquals("RUNTIME_ERROR",model.state.value.answer?.state) }
        fun click(tag:String) {
            val previous=model.state.value
            compose.onNodeWithTag(tag).performScrollTo().performClick()
            // All tagged clicks in this method invoke a ViewModel action.
            // Observe the action's state transition before testing its completion.
            compose.waitUntil(30_000) { model.state.value !== previous }
        }
        fun passed(name:String) { cases.put(JSONObject().put("id",name).put("passed",true)) }
        try {
            val input=File(context.cacheDir,"source-ui-$id.kpack")
            try {
                instrument.context.assets.open("walking-skeleton.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
                ProductSession(context,root,ProductConfiguration.keys(context),true).use { it.registry.activate(input) }
            } finally { input.delete() }
            scenario=ActivityScenario.launch(Intent(context,MainActivity::class.java).putExtra("packrag.debug.uiTestId",id).putExtra("packrag.debug.uiTestFontScale",2f).putExtra("packrag.debug.uiTestWidthDp",320))
            ProductUiTestSupport.awaitForeground(scenario!!)
            scenario!!.onActivity { model=ViewModelProvider(it)[PackRagViewModel::class.java] };settle()
            compose.onNodeWithTag("query-question").performScrollTo().performTextReplacement("What is the maximum continuous operating temperature of the Aster-9?")
            compose.onNodeWithTag("query-date").performScrollTo().performTextReplacement("2027-01-01");click("query-submit");settle()
            assertEquals("ANSWER_ACCEPTED",model.state.value.answer?.state)
            val captured=model.state.value;val record=captured.answer!!.sources.single();val pack=captured.installed.single()
            compose.onNodeWithText("[S1] Aster-9 · G0-D01").performScrollTo().performClick()
            compose.onNodeWithTag("source-details").performScrollTo().assertIsDisplayed()
            compose.onNodeWithText("Declared license: CC0-1.0").performScrollTo().assertIsDisplayed()
            compose.onNodeWithText("Canonical URI: Unknown").performScrollTo().assertIsDisplayed()
            compose.onNodeWithTag("source-canonical-text").performScrollTo().assertTextEquals(record.canonicalText)
            compose.onNodeWithTag("source-generator-text").performScrollTo().assertTextEquals("Generation used the exact canonical text above.")
            compose.onNodeWithText("Back to answer").performScrollTo().performClick()
            passed("actual-model-answer-captured-canonical-license-unknown-uri-and-generator-text")
            compose.onNodeWithText("Manage packs").performScrollTo().performClick();click("details-${pack.tag}");settle()
            compose.onNodeWithTag("pack-details-verified").performScrollTo().assertIsDisplayed()
            assertSame(captured.answer,model.state.value.answer);assertSame(captured.trace,model.state.value.trace);assertSame(captured.submission,model.state.value.submission)
            assertEquals(record.pack,model.state.value.details?.identity)
            passed("actual-active-details-reverified-and-original-answer-context-retained")
            click("deactivate-${pack.tag}");settle()
            assertNull(model.state.value.answer);assertNull(model.state.value.trace);assertNull(model.state.value.details)
            click("details-${pack.tag}");settle()
            compose.onNodeWithTag("pack-details-verified").performScrollTo().assertIsDisplayed();assertTrue(model.state.value.packs.isEmpty())
            compose.onNodeWithText("Currently inactive").performScrollTo().assertIsDisplayed()
            passed("same-deactivation-path-closes-context-inactive-details-do-not-activate")
            click("activate-${pack.tag}");settle();assertEquals(1,model.state.value.packs.size);assertNull(model.state.value.details)
            passed("same-explicit-activation-path-from-details")
            assertEquals(before,guard());passed("explicit-fifty-owner-public-files-unchanged")
            File(context.filesDir,"m4-source-details-ui.json").writeText(JSONObject().put("status","PASS").put("cases",cases)
                .put("actual_weight_inference",true).put("prefill_tokens",captured.trace!!.prefillTokens).put("evidence_tokens",captured.trace!!.evidenceTokens)
                .put("emitted_tokens",captured.trace!!.emittedTokens).put("owner_registry_and_model_sha256",JSONObject(before)).put("owner_guard_scope","EXPLICIT_50_PUBLIC_BASELINE_FILES_NO_ENUMERATION")
                .put("raw_reasoning_persisted",false).put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET").toString(2),Charsets.UTF_8)
        } finally { scenario?.close();cleanup(root) }
    }
    @Test fun verifiedArabicFrenchCanonicalAndEnglishRenderingComponentScreenshots() {
        assertTrue(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val assets=instrument.context.assets;val reference=assets.open("source-details-corpus/signed-row-expectations.json").bufferedReader().use { JSONObject(it.readText()) }
        val rows=reference.getJSONArray("packs");val cases=JSONArray();val before=guard()
        for((language,label) in listOf("ar" to "ar-reviewed","fr" to "fr-official")) {
            val expected=(0 until rows.length()).map { rows.getJSONObject(it) }.single { it.getString("asset")=="representation-corpus/$label-representation.kpack" }
            val id=UUID.randomUUID().toString();val root=File(context.filesDir,"ui-tests/$id");val readerRoot=File(context.filesDir,"source-language-${UUID.randomUUID()}")
            assertTrue(readerRoot.mkdirs());var scenario:ActivityScenario<MainActivity>?=null
            try {
                val input=File(readerRoot,"input.kpack");assets.open(expected.getString("asset")).use { source -> input.outputStream().use { source.copyTo(it) } }
                assertEquals(expected.getString("pack_sha256"),Crypto.fileHash(input))
                val key=assets.open(expected.getString("public_key_asset")).use { it.readBytes() };assertEquals(expected.getString("public_key_sha256"),Crypto.sha256(key))
                val lock=context.assets.open("toolchain.lock.json").bufferedReader().use { JSONObject(it.readText()) };val schema=context.assets.open("schema.sql").bufferedReader().use { it.readText() }
                val record=PackRegistry(File(readerRoot,"registry"),PackVerifier(listOf(key),lock.getJSONObject("embedder").getJSONObject("pack_profile"),schema,true)).use { registry ->
                    val pack=registry.activate(input);val chunk=pack.chunks.single();assertEquals(language,chunk.language)
                    val candidate=Candidate(pack,chunk,true,1,1,1.0,2.0/61,true)
                    SourceRecord("S1",chunk.canonicalText,chunk.sourceTitle,chunk.locator,chunk.publisher,candidate.packIdentity,
                        validityProvenance(chunk),ownedMetadata(sourceMetadata(chunk,pack.manifest.getJSONObject("publisher").getString("key_id"),pack.relations)),
                        canonicalLanguage=chunk.language,canonicalTextSha256=chunk.textSha256,generatorRepresentation=candidate.generatorRendering,
                        originalSha256=chunk.originalSha256,chunkId=chunk.id,sourceId=chunk.sourceId,originRecords=ownedList(listOf(candidate.captureOrigin())),
                        attribution=chunk.attribution,location=chunk.location)
                }
                scenario=ActivityScenario.launch(Intent(context,MainActivity::class.java).putExtra("packrag.debug.uiTestId",id).putExtra("packrag.debug.uiTestFontScale",2f).putExtra("packrag.debug.uiTestWidthDp",320))
                ProductUiTestSupport.awaitForeground(scenario!!)
                scenario!!.onActivity { activity -> activity.setContent {
                    MaterialTheme { Column(Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(24.dp)) { SourceScreen(record) } }
                } }
                compose.onNodeWithTag("source-canonical-text").performScrollTo().assertTextEquals(record.canonicalText).assertIsDisplayed()
                ProductUiTestSupport.foreground();val screenshot=requireNotNull(instrument.uiAutomation.takeScreenshot());val image=File(context.filesDir,"m4-source-details-$language.png")
                image.outputStream().use { assertTrue(screenshot.compress(Bitmap.CompressFormat.PNG,100,it)) };screenshot.recycle()
                compose.onNodeWithTag("source-generator-text").performScrollTo().assertTextEquals(record.generatorRepresentation!!.text)
                cases.put(JSONObject().put("language",language).put("canonical_sha256",record.canonicalTextSha256)
                    .put("rendering_sha256",record.generatorRepresentation!!.textSha256).put("manifest_sha256",record.pack.manifestSha256)
                    .put("screenshot",image.name).put("screenshot_sha256",Crypto.fileHash(image)).put("passed",true))
            } finally {
                scenario?.close();cleanup(root);require(readerRoot.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));assertTrue(readerRoot.deleteRecursively())
            }
        }
        assertEquals(before,guard())
        File(context.filesDir,"m4-source-details-languages-ui.json").writeText(JSONObject().put("status","PASS").put("cases",cases)
            .put("scope","Viewer component set as Activity content using actual verified signed AR/FR records after reader close; no new model inference or production app admission of these custom-key fixtures. Real foreign-canonical generation is the retained representation runtime gate.")
            .put("owner_registry_and_model_sha256",JSONObject(before)).put("owner_guard_scope","EXPLICIT_50_PUBLIC_BASELINE_FILES_NO_ENUMERATION").put("raw_reasoning_persisted",false).toString(2),Charsets.UTF_8)
    }
}
