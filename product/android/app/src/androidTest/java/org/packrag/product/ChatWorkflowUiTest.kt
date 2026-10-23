package org.packrag.product

import android.provider.DocumentsContract
import android.view.KeyEvent
import android.view.accessibility.AccessibilityNodeInfo
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.v2.createEmptyComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.packs.PackImportStage
import org.packrag.packs.PackImportState
import org.json.JSONArray
import java.io.File

/** Real system document picker and its separate-UID grants, with no direct import shortcut. */
@RunWith(AndroidJUnit4::class)
class ChatWorkflowUiTest {
    @get:Rule val compose=createEmptyComposeRule()
    private val support get()=ProductUiTestSupport
    private fun record(name:String,ids:List<String>,before:Map<String,String>,images:JSONObject,extra:JSONObject) {
        assertEquals(before,ChatRepairOwner.snapshot())
        java.io.File(support.context.filesDir,name).writeText(extra.put("status","PASS").put("cases",org.json.JSONArray(ids))
            .put("visual_png",images).put("owner_sha256",JSONObject(before)).put("controlled_file_count",before.size)
            .put("owner_guard_scope",if(before.size==5) "FRESH_EMULATOR_FOUR_MODELS_ONE_FIXTURE_DEFAULT_REGISTRIES_ABSENT" else "PHYSICAL_EXPLICIT_50_PUBLIC_BASELINE_PLUS_ONE_FIXTURE")
            .put("actual_weight_inference",false).put("scope","Current real MainActivity picker/registry UI; separate-provider grant and observed import stages. Original PNG review required; not human calibration or full M4.")
            .toString(2),Charsets.UTF_8)
    }
    @Test fun largeFontLifecycleFiltersAndLocalAssetPicker() {
        val before=ChatRepairOwner.snapshot();val images=JSONObject();val cases=mutableListOf<String>()
        support.activity(ProductUiLayout(2f,320),prepare={root ->
            root.mkdirs()
            ProductSession(support.context,root,ProductConfiguration.keys(support.context),true).use{session ->
                for(name in listOf("v1","v2")) {
                    val input=File(root,"seed-$name.kpack")
                    try {support.instrument.context.assets.open("lifecycle-corpus/$name.kpack").use{src->input.outputStream().use{src.copyTo(it)}};session.registry.activate(input)}
                    finally{input.delete()}
                }
            }
        }) { scenario,model ->
            fun settle(){support.ready(compose,model)}
            fun click(tag:String){
                val node=compose.onNodeWithTag(tag)
                if(runCatching{node.assertIsDisplayed()}.isFailure)node.performScrollTo()
                node.assertIsDisplayed().performClick();settle()
            }
            fun active(version:String?){assertEquals(version,model.state.value.installed.singleOrNull{it.active}?.version)}
            fun edit(tag:String,value:String){
                val node=compose.onNodeWithTag(tag)
                node.performScrollTo().performClick();compose.waitForIdle()
                node.performTextReplacement(value);compose.waitForIdle()
                assertEquals("Entered $tag",value,node.fetchSemanticsNode().config[androidx.compose.ui.semantics.SemanticsProperties.EditableText].text)
            }
            val id="org.packrag.development.walking-skeleton"
            fun tag(action:String,version:String)="$action-$id@$version"
            settle();active("1.0.1");click("manage-packs")
            click(tag("activate","1.0.0"));compose.onNodeWithText("Older content").assertIsDisplayed();active("1.0.1")
            images.put("m4-chat-older-warning.png",support.screenshot(compose,"m4-chat-older-warning.png"))
            click("cancel-pack-change");active("1.0.1")
            click(tag("rollback","1.0.1"));click("confirm-pack-change");active("1.0.0")
            assertEquals("1.0.1",model.state.value.installed.single{it.active}.newest)
            cases.add("older-version-cancel-and-explicit-rollback-preserve-newest-history")
            click(tag("activate","1.0.1"));click(tag("remove","1.0.1"));click("cancel-pack-change");active("1.0.1")
            click(tag("remove","1.0.1"));click("confirm-pack-change");active(null)
            assertEquals(listOf("1.0.0"),model.state.value.installed.map{it.version})
            cases.add("removal-cancel-confirm-no-automatic-fallback")
            click("packs-back-answer");click("query-controls-toggle")
            edit("query-date","2028-02-29")
            edit("query-jurisdiction","MA-01")
            support.hideKeyboard(scenario)
            compose.waitForIdle()
            assertEquals("Jurisdiction after keyboard hide","MA-01",compose.onNodeWithTag("query-jurisdiction").fetchSemanticsNode().config[androidx.compose.ui.semantics.SemanticsProperties.EditableText].text)
            compose.onNodeWithTag("query-jurisdiction").performScrollTo().assertIsDisplayed()
            images.put("m4-chat-large-jurisdiction.png",support.screenshot(compose,"m4-chat-large-jurisdiction.png"))
            compose.onNodeWithTag("query-current-law").performScrollTo().performClick()
            images.put("m4-chat-large-law-toggle.png",support.screenshot(compose,"m4-chat-large-law-toggle.png"))
            click("query-controls-toggle")
            click("query-controls-toggle")
            assertEquals("Jurisdiction after filter closure/reopen","MA-01",compose.onNodeWithTag("query-jurisdiction").fetchSemanticsNode().config[androidx.compose.ui.semantics.SemanticsProperties.EditableText].text)
            click("query-controls-toggle")
            compose.onNodeWithTag("query-question").performTextReplacement("Which repair instructions are available?")
            support.hideKeyboard(scenario);click("query-submit")
            compose.waitUntil(30_000){model.state.value.completedResultId!=null && !model.state.value.busy}
            assertEquals("NO_ACTIVE_PACK",model.state.value.answer?.state);assertEquals(0,model.state.value.trace!!.emittedTokens)
            assertEquals("2028-02-29",model.state.value.submission!!.query.asOf);assertEquals("MA-01",model.state.value.submission!!.query.jurisdiction)
            assertTrue(model.state.value.submission!!.query.currentLaw)
            cases.add("large-font-controls-captured-by-real-query-not-model-generation")
            scenario.recreate();support.awaitForeground(scenario);settle();assertEquals(1,model.turns.value.size)
            click("app-menu");click("diagnostics-toggle");click("app-menu")
            compose.onNodeWithText("Emitted tokens (includes terminal): 0").performScrollTo().assertIsDisplayed()
            images.put("m4-chat-visible-diagnostic-counts.png",support.screenshot(compose,"m4-chat-visible-diagnostic-counts.png"))
            cases.add("captured-zero-emission-diagnostics-visibly-readable-no-performance-inference")
            click("app-menu");click("local-assets-open");click("local-assets-check")
            assertTrue(model.state.value.localAssets.all{it.condition==LocalAssetCondition.VERIFIED})
            assertEquals(0,model.state.value.trace!!.emittedTokens)
            compose.onNodeWithTag("local-asset-TEMPLATE-observed-hash").performScrollTo().assertTextEquals("Observed SHA256: ${LocalAssetSlot.TEMPLATE.expectedSha256}")
            images.put("m4-chat-local-template.png",support.screenshot(compose,"m4-chat-local-template.png"))
            // Actual Android document picker cancellation must not alter pinned files.
            compose.onNodeWithTag("local-asset-import-TEMPLATE").performScrollTo().performClick()
            val picker=LocalAssetImportTestSupport.documentPickerPackage()
            compose.waitUntil(30_000){support.instrument.uiAutomation.rootInActiveWindow?.packageName?.toString()==picker}
            support.instrument.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK);support.awaitForeground(scenario);settle()
            assertNull(model.state.value.localAssetImport);assertTrue(model.state.value.localAssets.all{it.condition==LocalAssetCondition.VERIFIED})
            click("local-assets-back");assertEquals(1,model.turns.value.size)
            cases.add("exact-four-file-check-real-local-asset-picker-cancel-and-owned-answer-return")
            click("new-chat");assertTrue(model.turns.value.isEmpty());assertNull(model.state.value.completedResultId)
            assertEquals(listOf("1.0.0"),model.state.value.installed.map{it.version});active(null)
            cases.add("recreation-and-new-chat-keep-explicit-registry-state")
        }
        record("m4-chat-workflow-controls.json",cases,before,images,JSONObject().put("system_picker_executed",true).put("layout_font_scale",2).put("layout_width_dp",320))
    }
    @Test fun actualPickerCancellationSignedImportAndSafeRejectionExposeObservedStages() {
        val before=ChatRepairOwner.snapshot();val images=JSONObject()
        val expected=support.instrument.context.assets.open("pack-overview-corpus/expectations.json").bufferedReader().use {
            JSONObject(it.readText()).getJSONObject("fixtures").getJSONObject("release-trust-corpus/calibration-schema-only.kpack")
        }
        val uri=DocumentsContract.buildDocumentUri("org.packrag.product.test.asset-documents","signed-kpack")
        // Instrumentation executes under the target UID; a real picker selection must supply this grant.
        support.context.revokeUriPermission(uri,android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
        assertThrows(SecurityException::class.java) { support.context.contentResolver.openFileDescriptor(uri,"r")?.close() }
        support.activity { _,model ->
            support.ready(compose,model)
            val pickerPackage=LocalAssetImportTestSupport.documentPickerPackage()
            fun pickerVisible()=support.instrument.uiAutomation.rootInActiveWindow?.packageName?.toString()==pickerPackage
            fun until(predicate:()->Boolean) {
                val end=System.nanoTime()+30_000_000_000L
                while(!predicate() && System.nanoTime()<end)android.os.SystemClock.sleep(50)
                assertTrue("Expected bounded picker/app transition",predicate())
            }
            fun find(node:AccessibilityNodeInfo?,labels:Set<String>,depth:Int=0):AccessibilityNodeInfo? {
                if(node==null || depth>30) return null
                if(node.text?.toString() in labels || node.contentDescription?.toString() in labels)return node
                for(i in 0 until node.childCount)find(node.getChild(i),labels,depth+1)?.let { return it }
                return null
            }
            fun systemClick(labels:Set<String>) {
                until { pickerVisible() && find(support.instrument.uiAutomation.rootInActiveWindow,labels)!=null }
                var node=requireNotNull(find(support.instrument.uiAutomation.rootInActiveWindow,labels));var levels=0
                while(!node.isClickable && levels++<5)node=requireNotNull(node.parent)
                assertTrue(node.performAction(AccessibilityNodeInfo.ACTION_CLICK))
            }
            fun launch() {
                support.foreground();compose.onNodeWithTag("import-kpack").performScrollTo().performClick();until { pickerVisible() }
            }
            fun select(label:String) {
                launch()
                if(find(support.instrument.uiAutomation.rootInActiveWindow,setOf(label))==null) {
                    if(find(support.instrument.uiAutomation.rootInActiveWindow,setOf("PackRAG test assets"))==null)
                        systemClick(setOf("Show roots","Afficher les racines"))
                    systemClick(setOf("PackRAG test assets"))
                }
                systemClick(setOf(label));until { support.instrument.uiAutomation.rootInActiveWindow?.packageName?.toString()=="org.packrag.product" }
                support.ready(compose,model)
            }
            launch();support.instrument.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK)
            until { support.instrument.uiAutomation.rootInActiveWindow?.packageName?.toString()=="org.packrag.product" }
            support.ready(compose,model);assertTrue(model.state.value.installed.isEmpty());assertTrue(model.state.value.packImportEvents.isEmpty())
            select("Signed synthetic test pack.kpack")
            val accepted=model.state.value;assertNull(accepted.answer);assertEquals(1,accepted.packs.size)
            assertEquals(expected.getString("manifest_sha256"),accepted.installed.single { it.active }.hash)
            assertEquals(PackImportStage.entries.toList(),accepted.packImportEvents.map { it.stage })
            assertTrue(accepted.packImportEvents.all { it.state==PackImportState.PASSED })
            support.context.contentResolver.openFileDescriptor(uri,"r")!!.use { }
            compose.onNodeWithTag("pack-import-details").performScrollTo().performClick()
            compose.onNodeWithTag("pack-import-SNAPSHOT_COPY").performScrollTo().assertTextContains("Completed",substring=true)
            compose.onNodeWithTag("pack-import-PAYLOAD_INTEGRITY").performScrollTo().assertTextEquals(
                "Payload verification (uncompressed bytes): Completed · 85076 / 85076 bytes")
            images.put("m4-f3-kpack-stages.png",support.screenshot(compose,"m4-f3-kpack-stages.png"))
            compose.onNodeWithTag("pack-import-REGISTRY_COMMIT").performScrollTo().assertTextEquals("Registry activation: Completed")
            images.put("m4-f3-kpack-activation.png",support.screenshot(compose,"m4-f3-kpack-activation.png"))
            select("Invalid synthetic test pack.kpack")
            val failed=model.state.value;assertEquals("RUNTIME_ERROR",failed.answer?.state);assertEquals(accepted.packs,failed.packs)
            assertTrue(failed.message.startsWith("ARCHIVE_REJECTED:"));assertFalse(failed.message.contains("/data/") || failed.message.contains("<"))
            assertEquals(PackImportState.REJECTED,failed.packImportEvents.last().state)
            compose.onNodeWithTag("operation-status").performScrollTo().assertTextContains("ARCHIVE_REJECTED:",substring=true)
            images.put("m4-f3-kpack-rejection.png",support.screenshot(compose,"m4-f3-kpack-rejection.png"))
        }
        record("m4-chat-workflow-picker.json",listOf("separate-provider-document-denied-before-real-system-picker-grant",
            "actual-picker-cancel-leaves-empty-registry-and-no-fabricated-stages","actual-picker-signed-synthetic-pack-import-and-full-identity",
            "visible-real-completed-stages-and-independent-transport-payload-byte-domains","actual-malformed-picker-document-safe-rejection-prior-active-preserved",
            "explicit-controlled-public-files-preserved"),before,images,JSONObject().put("system_picker_executed",true).put("manual_read_grant_shortcut",false)
                .put("approved_fixture_scope","SYNTHETIC_CALIBRATION_SCHEMA_ONLY_NOT_HUMAN_REVIEW"))
    }
}
