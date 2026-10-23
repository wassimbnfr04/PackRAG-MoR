package org.packrag.product

import android.content.Intent
import android.graphics.Bitmap
import android.os.SystemClock
import android.net.Uri
import android.view.accessibility.AccessibilityNodeInfo
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.v2.createEmptyComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.ViewModelStore
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import java.io.File
import java.nio.file.Files
import java.security.MessageDigest
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto

/** Separate real-picker visual gate. UI0004's native/result controls are not rerun or relabeled. */
@RunWith(AndroidJUnit4::class)
class LocalAssetImportVisualDeviceTest {
    @get:Rule val compose=createEmptyComposeRule()
    @Test fun actualPickerProgressCancelAndVerifiedTemplateHaveSettledFullWindowScreenshots() {
        assertTrue(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val support=LocalAssetImportTestSupport;val instrument=support.instrument;val context=support.context
        val before=support.ownerGuard();val root=File(context.filesDir,"f2-visual-${UUID.randomUUID()}")
        Files.createDirectory(root.toPath());val app=AssetImportPrivateApplication(context,root);val registry=File(root,"registry")
        val store=ViewModelStore();var scenario:ActivityScenario<MainActivity>?=null;lateinit var model:PackRagViewModel
        val cases=JSONArray();val images=JSONObject();val observations=JSONObject()
        val envelope=JSONObject().put("status","RUNNING").put("test_id",root.name).put("cases",cases)
        fun report(point:String){File(context.filesDir,"m4-local-asset-import-visual-progress.json").writeText(envelope.put("current_point",point).toString(2))}
        fun until(timeout:Long=30_000,predicate:()->Boolean){val end=SystemClock.elapsedRealtime()+timeout;while(!predicate() && SystemClock.elapsedRealtime()<end)SystemClock.sleep(20);assertTrue(predicate())}
        fun ready(){compose.waitForIdle();until{!model.state.value.busy};compose.waitForIdle();assertFalse(model.state.value.busy)}
        fun click(tag:String){compose.onNodeWithTag(tag).performScrollTo().performClick();compose.waitForIdle()}
        fun passed(id:String){cases.put(JSONObject().put("id",id).put("passed",true))}
        fun snapshot(name:String,copying:Boolean) {
            compose.waitForIdle();SystemClock.sleep(750)
            val exclusions=if(copying) listOf("local-asset-import-progress","local-asset-import-indicator").map{compose.onNodeWithTag(it).fetchSemanticsNode().boundsInRoot} else emptyList()
            var preceding:String?=null;var equalFrames=0;var attempts=0;val started=SystemClock.elapsedRealtime()
            while(SystemClock.elapsedRealtime()-started<10_000) {
                assertEquals(context.packageName,instrument.uiAutomation.rootInActiveWindow?.packageName?.toString())
                var width=0;var height=0;scenario!!.onActivity{width=it.window.decorView.width;height=it.window.decorView.height}
                val bytesBefore=model.state.value.localAssetImport?.copiedBytes
                val bitmap=requireNotNull(instrument.uiAutomation.takeScreenshot());attempts++
                try {
                    assertEquals(width,bitmap.width);assertEquals(height,bitmap.height)
                    // Only fingerprint static content. The actual unmodified PNG retains changing bytes/progress.
                    val hash=MessageDigest.getInstance("SHA-256")
                    for(y in 128 until bitmap.height-160 step 16)for(x in 0 until bitmap.width step 16) {
                        if(exclusions.none{x>=it.left-8 && x<=it.right+8 && y>=it.top-8 && y<=it.bottom+8}) {
                            val pixel=bitmap.getPixel(x,y);hash.update(byteArrayOf((pixel ushr 24).toByte(),(pixel ushr 16).toByte(),(pixel ushr 8).toByte(),pixel.toByte()))
                        }
                    }
                    val fingerprint=hash.digest().joinToString(""){"%02x".format(it)}
                    equalFrames=if(fingerprint==preceding)equalFrames+1 else 1;preceding=fingerprint
                    if(equalFrames>=3) {
                        val file=File(context.filesDir,name);file.outputStream().use{assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,it))}
                        images.put(name,JSONObject().put("sha256",Crypto.fileHash(file)).put("bytes",file.length()))
                        observations.put(name,JSONObject().put("equal_static_frames",equalFrames).put("samples",attempts)
                            .put("sample_interval_ms",250).put("minimum_post_picker_wait_ms",750).put("settling_ms",SystemClock.elapsedRealtime()-started)
                            .put("width",bitmap.width).put("height",bitmap.height).put("static_grid_sha256",fingerprint)
                            .put("status_navigation_margins_excluded_px",JSONArray(listOf(128,160)))
                            .put("excluded_dynamic_rectangles",JSONArray(exclusions.map{listOf(it.left,it.top,it.right,it.bottom)}))
                            .put("copied_bytes_before_sample",bytesBefore ?: JSONObject.NULL)
                            .put("copied_bytes_after_sample",model.state.value.localAssetImport?.copiedBytes ?: JSONObject.NULL))
                        return
                    }
                }finally{bitmap.recycle()}
                SystemClock.sleep(250)
            }
            error("Product screenshot did not settle; do not accept picker transition images")
        }
        try {
            report("PREPARING");support.grant("GRANT_CASES")
            ProductSession(app,registry,ProductConfiguration.keys(context),true).use{
                it.importLocalAsset(LocalAssetSlot.TEMPLATE,Uri.parse("content://org.packrag.product.test.asset-fixtures/template-valid"))
                assertNull(it.generatorLoadAndVerificationMs)
            }
            instrument.runOnMainSync{model=PackRagViewModel(app,registry);store.put("isolated",model)};ready()
            val launchId=UUID.randomUUID().toString()
            scenario=ActivityScenario.launch(Intent(context,MainActivity::class.java).putExtra("packrag.debug.uiTestId",launchId))
            scenario!!.onActivity{val old=ViewModelProvider(it)[PackRagViewModel::class.java];val key=it.viewModelStore.keys().single{key->it.viewModelStore[key]===old};it.viewModelStore.put(key,model)}
            scenario!!.recreate();scenario!!.onActivity{assertSame(model,ViewModelProvider(it)[PackRagViewModel::class.java])};ready();click("local-assets-open")
            val picker=support.documentPickerPackage()
            fun find(node:AccessibilityNodeInfo?,label:String,depth:Int=0):AccessibilityNodeInfo? {
                if(node==null || depth>30)return null
                if(node.text?.toString()==label || node.contentDescription?.toString()==label)return node
                for(i in 0 until node.childCount){val result=find(node.getChild(i),label,depth+1);if(result!=null)return result};return null
            }
            fun systemClick(label:String) {
                until(15_000){instrument.uiAutomation.rootInActiveWindow?.packageName?.toString()==picker && find(instrument.uiAutomation.rootInActiveWindow,label)!=null}
                var node=requireNotNull(find(instrument.uiAutomation.rootInActiveWindow,label));var depth=0
                while(!node.isClickable && depth++<5)node=requireNotNull(node.parent)
                assertTrue(node.performAction(AccessibilityNodeInfo.ACTION_CLICK))
            }
            fun choose(label:String) {
                click("local-asset-import-TEMPLATE");until(15_000){instrument.uiAutomation.rootInActiveWindow?.packageName?.toString()==picker}
                if(find(instrument.uiAutomation.rootInActiveWindow,label)==null){if(find(instrument.uiAutomation.rootInActiveWindow,"PackRAG test assets")==null)systemClick("Show roots");systemClick("PackRAG test assets")}
                systemClick(label);until(15_000){instrument.uiAutomation.rootInActiveWindow?.packageName?.toString()==context.packageName}
            }
            report("ACTUAL_SLOW_PICKER_COPY");choose("Slow template.jinja")
            until(15_000){model.state.value.localAssetImport?.copiedBytes?.let{it in 1..5442}==true}
            compose.onNodeWithTag("local-asset-import-progress").performScrollTo().assertTextContains("5443 bytes",substring=true)
            snapshot("m4-local-asset-import-visual-progress.png",true)
            assertTrue(model.state.value.localAssetImport!!.copiedBytes in 1..5442)
            click("local-asset-import-cancel");ready();assertTrue(model.state.value.message.contains("cancelled"))
            assertEquals(LocalAssetSlot.TEMPLATE.expectedSha256,Crypto.fileHash(File(root,"models/chat_template.jinja")))
            assertFalse(File(root,"models/.asset-import-v1").exists());passed("actual-picker-copy-settled-progress-and-cooperative-cancel")
            report("ACTUAL_OFFICIAL_PICKER_IMPORT");choose("Official template.jinja");ready()
            assertTrue(model.state.value.message.contains("installed and verified"))
            assertEquals(LocalAssetCondition.VERIFIED,model.state.value.localAssets.single{it.spec.slot==LocalAssetSlot.TEMPLATE}.condition)
            compose.onNodeWithTag("local-asset-TEMPLATE").performScrollTo().assertTextContains("Exact size and SHA256",substring=true)
            snapshot("m4-local-asset-import-visual-verified.png",false);passed("actual-picker-verified-template-settled-full-window")
            assertEquals(before,support.ownerGuard());passed("known-fifty-owner-public-files-unchanged")
            envelope.put("status","PASS").put("variant",BuildConfig.BUILD_TYPE).put("visual_png",images).put("frame_observations",observations)
                .put("owner_registry_and_model_sha256",JSONObject(before)).put("guards_unchanged",true).put("actual_weight_inference",false)
                .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET")
                .put("limits","Separate actual picker/template visual scope with static-grid settling and exact unmodified PNGs requiring independent visual review. Template only in isolated root; other assets unchecked/missing. UI0004 real native and completed-answer controls are retained separately under identical product and selected source proof. No new native/performance/gold/full F2/M4/release acceptance. Empty launch registry retained.")
            File(context.filesDir,"m4-local-asset-import-visual.json").writeText(envelope.toString(2));report("COMPLETED")
        }catch(failure:Throwable){envelope.put("status","FAIL").put("failure_type",failure.javaClass.simpleName);report("FAILED");throw failure}
        finally {
            scenario?.close();instrument.runOnMainSync{store.clear()}
            var released=false;val end=SystemClock.elapsedRealtime()+15_000
            while(!released && SystemClock.elapsedRealtime()<end){released=runCatching{ProductSession(app,registry,ProductConfiguration.keys(context),true).use{};true}.getOrDefault(false);if(!released)SystemClock.sleep(20)}
            check(released);support.deleteOwned(root,"f2-visual-")
        }
    }
}
