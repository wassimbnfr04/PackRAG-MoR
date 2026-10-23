package org.packrag.product

import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.net.Uri
import android.os.Process
import android.os.ParcelFileDescriptor
import android.provider.DocumentsContract
import android.view.KeyEvent
import android.view.WindowInsets
import android.view.accessibility.AccessibilityNodeInfo
import android.view.inputmethod.InputMethodManager
import android.content.Context
import android.app.Activity
import android.app.Application
import android.os.Bundle
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.v2.createEmptyComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.ViewModelStore
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import java.io.File
import java.nio.file.Files
import java.util.UUID
import java.util.concurrent.atomic.AtomicReference
import java.util.concurrent.atomic.AtomicBoolean
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto

/** Fresh authorized foreground window only: real Android picker, isolated real files and JNI. */
@RunWith(AndroidJUnit4::class)
class LocalAssetImportUiDeviceTest {
    @get:Rule val compose=createEmptyComposeRule()
    @Test fun actualSystemPickerCancelCorruptProgressCancelRecreationAndVerifiedImportKeepResult() {
        assertTrue(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val support=LocalAssetImportTestSupport;val instrument=support.instrument;val context=support.context
        val before=support.ownerGuard();val root=File(context.filesDir,"f2-import-ui-${UUID.randomUUID()}");Files.createDirectory(root.toPath())
        val app=AssetImportPrivateApplication(context,root);val registry=File(root,"registry");val standalone=ViewModelStore()
        var scenario:ActivityScenario<MainActivity>?=null;var launchedRegistry:File?=null
        lateinit var model:PackRagViewModel;val cases=JSONArray();val images=JSONObject()
        val envelope=JSONObject().put("status","RUNNING").put("test_id",root.name).put("cases",cases)
        val launchId=UUID.randomUUID().toString()
        val host=AtomicReference<MainActivity>();val restoredBundle=AtomicBoolean(false)
        val realApplication=context.applicationContext as Application
        val lifecycle=object:Application.ActivityLifecycleCallbacks {
            override fun onActivityCreated(activity:Activity,savedInstanceState:Bundle?) {
                if(activity is MainActivity && activity.intent.getStringExtra("packrag.debug.uiTestId")==launchId) {
                    restoredBundle.set(savedInstanceState!=null);host.set(activity)
                }
            }
            override fun onActivityStarted(activity:Activity){}
            override fun onActivityResumed(activity:Activity){}
            override fun onActivityPaused(activity:Activity){}
            override fun onActivityStopped(activity:Activity){}
            override fun onActivitySaveInstanceState(activity:Activity,outState:Bundle){}
            override fun onActivityDestroyed(activity:Activity){}
        }
        realApplication.registerActivityLifecycleCallbacks(lifecycle)
        fun progress(point:String){File(context.filesDir,"m4-local-asset-import-ui-progress.json").writeText(envelope.put("current_point",point).toString(2),Charsets.UTF_8)}
        fun until(timeout:Long=600_000,predicate:()->Boolean){val end=System.nanoTime()+timeout*1_000_000;while(!predicate() && System.nanoTime()<end)android.os.SystemClock.sleep(20);assertTrue(predicate())}
        fun ready(){until{!model.state.value.busy};compose.waitForIdle();assertNull(model.state.value.localAssetImport)}
        fun passed(id:String){cases.put(JSONObject().put("id",id).put("passed",true))}
        fun click(tag:String){compose.onNodeWithTag(tag).performScrollTo().performClick()}
        fun snapshot(name:String){val bitmap=requireNotNull(instrument.uiAutomation.takeScreenshot());val file=File(context.filesDir,name)
            try{file.outputStream().use{assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,it))}}finally{bitmap.recycle()}
            images.put(name,JSONObject().put("sha256",Crypto.fileHash(file)).put("bytes",file.length()))}
        val document=DocumentsContract.buildDocumentUri("org.packrag.product.test.asset-documents","full-template")
        try {
            progress("BACKGROUND_PREPARATION");assertTrue(android.os.StatFs(root.absolutePath).availableBytes>=LocalAssetSlot.entries.sumOf{it.expectedBytes}+64L*1024*1024)
            envelope.put("grant_full_for_background_setup_only",support.grant("GRANT_FULL_ASSETS"))
            ProductSession(app,registry,ProductConfiguration.keys(context),true).use { session ->
                for(slot in LocalAssetSlot.entries)session.importLocalAsset(slot,Uri.parse("content://org.packrag.product.test.asset-fixtures/full-${slot.name.lowercase()}"))
                val pack=File(root,"input.kpack");instrument.context.assets.open("walking-skeleton.kpack").use{source->pack.outputStream().use{source.copyTo(it)}}
                assertEquals("19da286b9f0860c312dc8d14ce0ee8681bf12ca092a7b8a12171fd86abe02c7f",Crypto.fileHash(pack));session.registry.activate(pack)
            }
            instrument.runOnMainSync{model=PackRagViewModel(app,registry);standalone.put("isolated",model)}
            until{!model.state.value.busy};instrument.runOnMainSync{model.ask("What is the maximum continuous operating temperature of the Aster-9?","2027-01-01","",true)}
            until{!model.state.value.busy};val original=model.state.value
            assertEquals("ANSWER_ACCEPTED",original.answer?.state);assertNotNull(original.completedResultId)
            fun preserved(){assertSame(original.answer,model.state.value.answer);assertSame(original.trace,model.state.value.trace);assertSame(original.submission,model.state.value.submission);assertEquals(original.completedResultId,model.state.value.completedResultId)
                assertEquals(LocalAssetSlot.TEMPLATE.expectedSha256,Crypto.fileHash(File(root,"models/chat_template.jinja")));assertFalse(File(root,"models/.asset-import-v1").exists())}
            assertEquals(PackageManager.PERMISSION_DENIED,context.checkUriPermission(document,Process.myPid(),Process.myUid(),Intent.FLAG_GRANT_READ_URI_PERMISSION))
            assertThrows(SecurityException::class.java){context.contentResolver.openFileDescriptor(document,"r")?.close()}
            passed("actual-document-read-denied-before-system-picker-grant")
            launchedRegistry=File(context.filesDir,"ui-tests/$launchId")
            progress("ACTIVITY_LAUNCH")
            scenario=ActivityScenario.launch(Intent(context,MainActivity::class.java).putExtra("packrag.debug.uiTestId",launchId))
            ProductUiTestSupport.awaitForeground(scenario!!)
            scenario!!.onActivity { activity ->
                val previous=ViewModelProvider(activity)[PackRagViewModel::class.java]
                val key=activity.viewModelStore.keys().single{activity.viewModelStore[it]===previous}
                envelope.put("actual_viewmodel_store_key",key.toString());activity.viewModelStore.put(key,model)
            }
            // A new Activity reads the actual replaced store entry instead of its old lazy delegate.
            scenario!!.recreate();ProductUiTestSupport.awaitForeground(scenario!!);scenario!!.onActivity{assertSame(model,ViewModelProvider(it)[PackRagViewModel::class.java])};ready();preserved()
            click("local-assets-open");for(slot in LocalAssetSlot.entries)compose.onNodeWithTag("local-asset-import-${slot.name}").performScrollTo().assertIsDisplayed()
            val pickerIntent=Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("*/*")
            val targetLookup=context.packageManager.resolveActivity(pickerIntent,PackageManager.MATCH_DEFAULT_ONLY)?.activityInfo?.packageName
            val pickerPackage=targetLookup ?: support.documentPickerPackage()
            envelope.put("target_picker_lookup",targetLookup ?: JSONObject.NULL).put("picker_package_lookup_source",if(targetLookup==null)"SHELL_EXPLICIT_OPEN_DOCUMENT_OCTET_STREAM" else "TARGET_OPEN_DOCUMENT_ALL_MIMES")
            assertNotEquals(context.packageName,pickerPackage);envelope.put("resolved_picker_package",pickerPackage)
            fun pickerVisible():Boolean=instrument.uiAutomation.rootInActiveWindow?.packageName?.toString()==pickerPackage
            fun find(node:AccessibilityNodeInfo?,label:String,depth:Int=0):AccessibilityNodeInfo? {
                if(node==null || depth>30)return null
                if(node.text?.toString()==label || node.contentDescription?.toString()==label)return node
                for(i in 0 until node.childCount){val result=find(node.getChild(i),label,depth+1);if(result!=null)return result};return null
            }
            fun systemClick(label:String) {
                until(15_000){pickerVisible() && find(instrument.uiAutomation.rootInActiveWindow,label)!=null}
                var node=requireNotNull(find(instrument.uiAutomation.rootInActiveWindow,label));var levels=0
                while(!node.isClickable && levels++<5)node=requireNotNull(node.parent)
                assertTrue(node.performAction(AccessibilityNodeInfo.ACTION_CLICK))
            }
            fun choose(label:String,recreate:Boolean=false) {
                click("local-asset-import-TEMPLATE");until(15_000){pickerVisible()}
                if(recreate) {
                    // ActivityScenario.recreate() requires RESUMED and cannot model a caller stopped behind a picker.
                    val previous=requireNotNull(host.get());var requestedState=""
                    instrument.runOnMainSync{requestedState=previous.lifecycle.currentState.name;previous.recreate()}
                    until(15_000){previous.isDestroyed && host.get()?.let{it!==previous && !it.isDestroyed}==true}
                    assertTrue(restoredBundle.get());until(15_000){pickerVisible()}
                    instrument.runOnMainSync{assertSame(model,ViewModelProvider(requireNotNull(host.get()))[PackRagViewModel::class.java])}
                    envelope.put("pending_picker_recreation",JSONObject().put("requested_lifecycle_state",requestedState)
                        .put("previous_activity_destroyed",true).put("distinct_activity_created",true)
                        .put("saved_state_bundle_present",true).put("same_viewmodel",true).put("picker_still_foreground",true))
                }
                // Read actual picker accessibility nodes; never interact with a different foreground package.
                if(find(instrument.uiAutomation.rootInActiveWindow,label)==null) {
                    if(find(instrument.uiAutomation.rootInActiveWindow,"PackRAG test assets")==null)systemClick("Show roots")
                    systemClick("PackRAG test assets")
                }
                systemClick(label)
                until(15_000){instrument.uiAutomation.rootInActiveWindow?.packageName?.toString()==context.packageName}
            }
            progress("PICKER_CANCEL");click("local-asset-import-TEMPLATE");until(15_000){pickerVisible()}
            instrument.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK);until(15_000){instrument.uiAutomation.rootInActiveWindow?.packageName?.toString()==context.packageName};ready();preserved()
            passed("actual-system-picker-cancel-keeps-file-and-completed-result")
            progress("CORRUPT_DOCUMENT");choose("Corrupt template.jinja");ready();preserved()
            assertTrue(model.state.value.message.contains("LOCAL_ASSET_IMPORT_HASH_MISMATCH"));compose.onNodeWithTag("local-assets-message").performScrollTo().assertTextContains("rejected",substring=true)
            passed("actual-picked-corrupt-file-rejected-without-replacing-file-or-completion")
            progress("SLOW_DOCUMENT_CANCEL");choose("Slow template.jinja")
            until(15_000){model.state.value.localAssetImport?.copiedBytes?.let{it in 1..5442}==true}
            compose.onNodeWithTag("local-asset-import-progress").performScrollTo().assertTextContains("5443 bytes",substring=true)
            envelope.put("ui_observed_partial_copy_bytes",model.state.value.localAssetImport!!.copiedBytes)
            snapshot("m4-local-asset-import-ui-progress.png");click("local-asset-import-cancel");until(15_000){!model.state.value.busy};ready();preserved()
            assertTrue(model.state.value.message.contains("cancelled"));passed("actual-displayed-byte-progress-and-ui-cancel-wait-for-cleanup")
            progress("OFFICIAL_DOCUMENT_PENDING_RECREATION");choose("Official template.jinja",true);ready();preserved()
            assertTrue(model.state.value.message.contains("installed and verified"));assertEquals(LocalAssetCondition.VERIFIED,model.state.value.localAssets.single{it.spec.slot==LocalAssetSlot.TEMPLATE}.condition)
            assertEquals(PackageManager.PERMISSION_GRANTED,context.checkUriPermission(document,Process.myPid(),Process.myUid(),Intent.FLAG_GRANT_READ_URI_PERMISSION))
            val descriptor=instrument.uiAutomation.executeShellCommand("run-as org.packrag.product.test cat files/f2-document-open-audit.json")
            val audit=ParcelFileDescriptor.AutoCloseInputStream(descriptor).bufferedReader().use{JSONObject(it.readText())}
            assertEquals("full-template",audit.getString("last_document_id"));assertEquals(Process.myUid(),audit.getInt("calling_uid"));assertNotEquals(Process.myUid(),audit.getInt("provider_uid"));assertEquals(document.toString(),audit.getString("document_uri"))
            envelope.put("actual_system_document_open",audit)
            compose.onNodeWithTag("local-asset-TEMPLATE").performScrollTo().assertTextContains("Exact size and SHA256",substring=true);snapshot("m4-local-asset-import-ui-verified.png")
            passed("actual-picker-slot-survives-pending-activity-recreation-and-granted-verified-import")
            scenario!!.recreate();ProductUiTestSupport.awaitForeground(scenario!!);scenario!!.onActivity{assertSame(model,ViewModelProvider(it)[PackRagViewModel::class.java])};ready();preserved()
            compose.onNodeWithTag("local-assets-title").performScrollTo().assertIsDisplayed();click("local-assets-back")
            compose.onNodeWithText("[S1] Aster-9 · G0-D01").performScrollTo().performClick()
            compose.onNodeWithText("The Aster-9 thermal controller has a maximum continuous operating temperature of 74 °C.").performScrollTo().assertIsDisplayed();click("source-back-answer");preserved()
            passed("asset-page-recreation-back-and-canonical-evidence-navigation-retain-completion")
            progress("ACTUAL_POST_IMPORT_UI_QUERY")
            compose.onNodeWithTag("query-question").performScrollTo().performTextReplacement("What is the maximum continuous operating temperature of the Aster-9?")
            compose.onNodeWithTag("query-date").performScrollTo().performTextReplacement("2027-01-01")
            scenario!!.onActivity{(it.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager).hideSoftInputFromWindow(it.window.decorView.windowToken,0)}
            until(10_000){var hidden=false;scenario!!.onActivity{hidden=it.window.decorView.rootWindowInsets?.isVisible(WindowInsets.Type.ime())!=true};hidden}
            compose.waitForIdle()
            compose.onNodeWithTag("query-question").assertTextContains("What is the maximum continuous operating temperature of the Aster-9?",substring=true)
            compose.onNodeWithTag("query-date").assertTextContains("2027-01-01",substring=true)
            compose.onNodeWithTag("query-submit").assertIsEnabled()
            click("query-submit");progress("ACTUAL_POST_IMPORT_UI_QUERY_TAP_DISPATCHED")
            // Touch delivery and coroutine start are asynchronous; never accept the preceding idle completion.
            until(10_000){model.state.value.busy || model.state.value.completedResultId!=original.completedResultId}
            envelope.put("new_query_dispatch_observed",true)
            ready();val after=model.state.value;val answer=requireNotNull(after.answer);val text=requireNotNull(answer.text);val trace=requireNotNull(after.trace)
            assertEquals("ANSWER_ACCEPTED",answer.state);assertTrue(text.contains("74 °C"));assertTrue(text.contains("[S1]"));assertFalse(text.contains("<think>"));assertFalse(text.contains("</think>"))
            assertNotEquals(original.completedResultId,after.completedResultId);assertTrue(trace.initializationMs>0);assertTrue(trace.diagnostics!!.generationCalled);assertTrue(trace.emittedTokens in 1..512)
            assertEquals("266af80f5d4da1dac500acd9a2bcc1fd2317b2caf49141ebb586280b9df49333",answer.sources.single().canonicalTextSha256)
            passed("actual-post-import-ui-query-cold-native-and-validated-cited-answer")
            assertEquals(before,support.ownerGuard());passed("known-owner-fifty-public-files-unchanged")
            envelope.put("status","PASS").put("variant",BuildConfig.BUILD_TYPE).put("visual_png",images).put("actual_weight_inference",true).put("raw_reasoning_persisted",false)
                .put("answer",text).put("emitted_tokens",trace.emittedTokens).put("initialization_ms",trace.initializationMs).put("completed_result_id_before",original.completedResultId).put("completed_result_id_after",after.completedResultId)
                .put("owner_registry_and_model_sha256",JSONObject(before)).put("guards_unchanged",true).put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET")
                .put("limits","Actual system DocumentsProvider grants/foreground Activity/cancellation/recreation/native synthetic scope. Test-only application/storage and library-group actual store-key injection. PNGs need independent visual inspection. No whole phone restart, arbitrary IPC bound, domain/gold/performance, full F2/M4/product/release acceptance.")
            File(context.filesDir,"m4-local-asset-import-ui.json").writeText(envelope.toString(2),Charsets.UTF_8);progress("COMPLETED")
        } catch(failure:Throwable){envelope.put("status","FAIL").put("failure_type",failure.javaClass.simpleName);File(context.filesDir,"m4-local-asset-import-ui-progress.json").writeText(envelope.toString(2),Charsets.UTF_8);throw failure}
        finally {
            scenario?.close();instrument.runOnMainSync{standalone.clear()}
            realApplication.unregisterActivityLifecycleCallbacks(lifecycle)
            var released=false;val end=System.nanoTime()+15_000_000_000L
            while(!released && System.nanoTime()<end){released=runCatching{ProductSession(app,registry,ProductConfiguration.keys(context),true).use{};true}.getOrDefault(false);if(!released)android.os.SystemClock.sleep(20)}
            check(released);support.deleteOwned(root,"f2-import-ui-")
            // Separately generated empty launch registry is retained, not recursively deleted.
            launchedRegistry?.let { owned ->
                require(owned.parentFile!!.canonicalFile==File(context.filesDir,"ui-tests").canonicalFile && owned.name.matches(Regex("[0-9a-f-]{36}")))
                // Its initially empty test registry may have an asynchronous old-session close; preserve it if still locked.
                runCatching{ProductSession(context,owned,ProductConfiguration.keys(context),true).use{}}
            }
        }
    }
}
