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

/** Real system document picker and its separate-UID grants, with no direct import shortcut. */
@RunWith(AndroidJUnit4::class)
class PackImportUiTest {
    @get:Rule val compose=createEmptyComposeRule()
    private val support get()=ProductUiTestSupport
    @Test fun actualPickerCancellationSignedImportAndSafeRejectionExposeObservedStages() {
        val before=LocalAssetImportTestSupport.ownerGuard();val images=JSONObject()
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
        support.record("m4-f3-kpack-picker-ui.json",listOf("separate-provider-document-denied-before-real-system-picker-grant",
            "actual-picker-cancel-leaves-empty-registry-and-no-fabricated-stages","actual-picker-signed-synthetic-pack-import-and-full-identity",
            "visible-real-completed-stages-and-independent-transport-payload-byte-domains","actual-malformed-picker-document-safe-rejection-prior-active-preserved",
            "fifty-owner-public-files-preserved"),before,images,JSONObject().put("system_picker_executed",true).put("manual_read_grant_shortcut",false)
                .put("approved_fixture_scope","SYNTHETIC_CALIBRATION_SCHEMA_ONLY_NOT_HUMAN_REVIEW"))
    }
}
