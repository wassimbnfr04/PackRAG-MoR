package org.packrag.product

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.view.inputmethod.InputMethodManager
import androidx.compose.ui.test.junit4.ComposeTestRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.ByteBuffer
import java.nio.file.Files
import java.security.MessageDigest
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.packrag.crypto.RawManifestVerifier as Crypto

/** New combined UI controls share exact foreground/settling/owned-root closure behavior. */
object ProductUiTestSupport {
    val instrument get()=InstrumentationRegistry.getInstrumentation()
    val context get()=instrument.targetContext
    fun foreground(){
        // A just-resumed Activity can precede the accessibility bridge's first window.
        // Wait only for an absent window; a different package must still fail immediately.
        val deadline=android.os.SystemClock.uptimeMillis()+5_000
        var packageName=instrument.uiAutomation.rootInActiveWindow?.packageName?.toString()
        while(packageName==null && android.os.SystemClock.uptimeMillis()<deadline) {
            android.os.SystemClock.sleep(50)
            packageName=instrument.uiAutomation.rootInActiveWindow?.packageName?.toString()
        }
        assertEquals("org.packrag.product",packageName)
    }
    fun awaitForeground(scenario:ActivityScenario<MainActivity>) {
        val deadline=android.os.SystemClock.uptimeMillis()+5_000
        var focusedResumed=false
        var packageName:String?=null
        do {
            scenario.onActivity {
                focusedResumed=it.window.decorView.hasWindowFocus() &&
                    it.lifecycle.currentState==androidx.lifecycle.Lifecycle.State.RESUMED
            }
            packageName=instrument.uiAutomation.rootInActiveWindow?.packageName?.toString()
            if(focusedResumed && packageName=="org.packrag.product")return
            android.os.SystemClock.sleep(50)
        } while(android.os.SystemClock.uptimeMillis()<deadline)
        assertTrue("Launched Activity did not become focused/resumed; accessibility package=$packageName",focusedResumed)
        assertEquals("org.packrag.product",packageName)
    }
    fun ready(compose:ComposeTestRule,model:PackRagViewModel) {
        compose.waitUntil(600_000){!model.state.value.busy};compose.waitForIdle();foreground()
    }
    fun hideKeyboard(scenario:ActivityScenario<MainActivity>) {
        scenario.onActivity { activity -> activity.currentFocus?.clearFocus()
            (activity.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager).hideSoftInputFromWindow(activity.window.decorView.windowToken,0) }
    }
    fun <T> activity(layout:ProductUiLayout?=null,prepare:(File)->Unit={},block:(ActivityScenario<MainActivity>,PackRagViewModel)->T):T {
        assertTrue(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val id=UUID.randomUUID().toString();val parent=File(context.filesDir,"ui-tests");val root=File(parent,id)
        assertFalse(Files.isSymbolicLink(parent.toPath()));assertFalse(root.exists())
        val intent=Intent(context,MainActivity::class.java).putExtra("packrag.debug.uiTestId",id)
        layout?.let { intent.putExtra("packrag.debug.uiTestFontScale",it.fontScale).putExtra("packrag.debug.uiTestWidthDp",it.maximumWidthDp) }
        var scenario:ActivityScenario<MainActivity>?=null
        var primaryFailure:Throwable?=null
        try {
            prepare(root)
            val launched=ActivityScenario.launch<MainActivity>(intent);scenario=launched
            awaitForeground(launched)
            lateinit var model:PackRagViewModel;launched.onActivity { model=ViewModelProvider(it)[PackRagViewModel::class.java] }
            return block(launched,model)
        } catch(failure:Throwable) {
            primaryFailure=failure;throw failure
        } finally {
            try {
            scenario?.close();val end=System.nanoTime()+10_000_000_000L;var released=false
            while(!released && System.nanoTime()<end) {
                released=runCatching { ProductSession(context,root,ProductConfiguration.keys(context),true).use { };true }.getOrDefault(false)
                if(!released)android.os.SystemClock.sleep(50)
            }
            check(released);require(root.canonicalPath.startsWith(parent.canonicalPath+File.separator))
            assertFalse(Files.isSymbolicLink(root.toPath()))
            Files.walk(root.toPath()).use { paths->require(paths.noneMatch { Files.isSymbolicLink(it) || it.fileName.toString()==".private" }) }
            assertTrue(root.deleteRecursively())
            } catch(cleanupFailure:Throwable) {
                val original=primaryFailure
                if(original!=null) original.addSuppressed(cleanupFailure) else throw cleanupFailure
            }
        }
    }
    fun screenshot(compose:ComposeTestRule,name:String):JSONObject {
        compose.waitForIdle();foreground();android.os.SystemClock.sleep(750)
        var prior:String?=null;var equal=0;var last:Bitmap?=null;var hash=""
        try {
            repeat(3) { index ->
                val bitmap=requireNotNull(instrument.uiAutomation.takeScreenshot());val digest=MessageDigest.getInstance("SHA-256")
                for(y in 128 until bitmap.height-160 step 24)for(x in 16 until bitmap.width-16 step 24)
                    digest.update(ByteBuffer.allocate(4).putInt(bitmap.getPixel(x,y)).array())
                hash=digest.digest().joinToString(""){"%02x".format(it)};equal=if(hash==prior)equal+1 else 1;prior=hash
                last?.recycle();last=bitmap;if(index<2)android.os.SystemClock.sleep(250)
            }
            assertEquals(3,equal);foreground();val bitmap=requireNotNull(last);val file=File(context.filesDir,name)
            file.outputStream().use { assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,it)) }
            return JSONObject().put("sha256",Crypto.fileHash(file)).put("bytes",file.length()).put("width",bitmap.width).put("height",bitmap.height)
                .put("equal_static_frames",3).put("static_grid_sha256",hash).put("sample_interval_ms",250).put("minimum_wait_ms",750)
                .put("settling_only_system_margins_px",JSONArray(listOf(128,160)))
        } finally { last?.recycle() }
    }
    fun record(name:String,ids:List<String>,before:Map<String,String>,images:JSONObject,extra:JSONObject=JSONObject()) {
        assertEquals(before,LocalAssetImportTestSupport.ownerGuard())
        File(context.filesDir,name).writeText(extra.put("status","PASS").put("cases",JSONArray(ids.map { JSONObject().put("id",it).put("passed",true) }))
            .put("visual_png",images).put("owner_registry_and_model_sha256",JSONObject(before)).put("owner_guard_scope","EXPLICIT_50_PUBLIC_BASELINE_FILES_NO_ENUMERATION")
            .put("raw_reasoning_persisted",false).put("actual_weight_inference",false)
            .put("scope","Actual isolated debug Activity physical UI. Original full settled PNGs require independent review. No global phone resource change, new model generation, genuine domain/calibration, screen-reader spoken-output or full milestone/release acceptance.").toString(2),Charsets.UTF_8)
    }
}
