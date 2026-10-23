package org.packrag.product

import android.app.Application
import android.content.ComponentName
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto

/** Instrumentable production-policy DEMO; explicitly not the final non-debuggable release. */
@RunWith(AndroidJUnit4::class)
class ProductionPolicyDeviceTest {
    @Test fun compiledDemoPolicyAndActualViewModelAdmissionHaveNoDevelopmentBypass() {
        val instrument=InstrumentationRegistry.getInstrumentation(); val context=instrument.targetContext
        assertEquals("demo",BuildConfig.BUILD_TYPE); assertFalse(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        assertTrue("Demo is explicitly instrumentable, not final release",BuildConfig.DEBUG)
        val info=context.packageManager.getPackageInfo(context.packageName,PackageManager.GET_PERMISSIONS)
        assertFalse(info.requestedPermissions?.contains("android.permission.INTERNET") ?: false)
        val names=context.assets.list("")!!.toSet()
        assertFalse("development-public-key.raw" in names); assertFalse("lifecycle-public-key.raw" in names)
        assertNotNull(runCatching { context.packageManager.getServiceInfo(ComponentName(context,"org.packrag.product.RegistryCrashProbeService"),0) }.exceptionOrNull())
        val approved=ProductConfiguration.approvedKeys(context)
        assertEquals(approved.map(Crypto::keyId),ProductConfiguration.keys(context).map(Crypto::keyId))
        assertNotNull(runCatching { ProductConfiguration.keys(context,true) }.exceptionOrNull())
        val expected=File(context.filesDir,"production-registry").canonicalFile
        assertEquals(expected,ProductConfiguration.defaultRoot(context).canonicalFile)
        for(value in listOf("not-a-uuid",UUID.randomUUID().toString(),"../../packs"))
            assertEquals(expected,ProductConfiguration.launchRoot(context,Intent().putExtra("packrag.debug.uiTestId",value)).canonicalFile)
        assertEquals("Ready.",ProductConfiguration.readyMessage())
        val owner=File(context.filesDir,"packs")
        fun ownerHashes()=if(!owner.exists()) emptyMap<String,String>() else owner.walkTopDown().filter { it.isFile }.associate { it.relativeTo(owner).path to Crypto.fileHash(it) }
        val before=ownerHashes(); val root=File(context.filesDir,"production-policy-${UUID.randomUUID()}")
        val input=File(context.cacheDir,"production-policy-${UUID.randomUUID()}.kpack")
        val store=ViewModelStore(); lateinit var model: PackRagViewModel
        val cases=instrument.context.assets.open("release-trust-corpus/cases.json").bufferedReader().use { JSONObject(it.readText()).getJSONArray("cases") }
        val results=JSONArray()
        fun waitReady() { val end=System.nanoTime()+30_000_000_000L; while(model.state.value.busy && System.nanoTime()<end) android.os.SystemClock.sleep(20); assertFalse(model.state.value.busy) }
        try {
            instrument.runOnMainSync { model=PackRagViewModel(context.applicationContext as Application,root); store.put("test",model) }; waitReady()
            assertTrue(model.state.value.packs.isEmpty())
            for(i in 0 until cases.length()) {
                val case=cases.getJSONObject(i)
                instrument.context.assets.open("release-trust-corpus/"+case.getString("filename")).use { source -> input.outputStream().use { source.copyTo(it) } }
                assertEquals(case.getString("sha256"),Crypto.fileHash(input))
                instrument.runOnMainSync { model.importPack(Uri.fromFile(input)) }; waitReady()
                if(case.getBoolean("accept_production")) {
                    assertEquals("Ready.",model.state.value.message); assertEquals(1,model.state.value.packs.size)
                } else {
                    assertEquals("RUNTIME_ERROR",model.state.value.answer?.state)
                    assertTrue(model.state.value.message,model.state.value.message.contains(case.getString("error_contains")))
                    assertEquals(1,model.state.value.packs.size)
                }
                assertNull(model.state.value.decision); assertEquals(case.getString("sha256"),Crypto.fileHash(input))
                results.put(JSONObject().put("id",case.getString("id")).put("passed",true))
            }
            assertEquals(before,ownerHashes())
            File(context.filesDir,"m3-production-policy.json").writeText(JSONObject().put("status","PASS").put("variant",BuildConfig.BUILD_TYPE)
                .put("development_mode",BuildConfig.ALLOW_DEVELOPMENT_PACKS).put("instrumentation_debuggable",BuildConfig.DEBUG)
                .put("no_internet_permission",true).put("development_key_assets_absent",true).put("crash_probe_service_absent",true)
                .put("debug_launch_routing_ignored",true).put("owner_development_registry_hashes_unchanged",true).put("viewmodel_admission_cases",results)
                .put("limits","Debug-certificate signed instrumentable DEMO of production admission policy; not final non-debuggable signed release acceptance. Positive calibration fields are schema-only fixtures. Actual inference is a separate retained core method.")
                .put("network_mode","MOBILE_DATA_PRESERVED").toString(2),Charsets.UTF_8)
        } finally {
            instrument.runOnMainSync { store.clear() }; input.delete()
            // onCleared closes the registry asynchronously. Wait for its file lease before cleanup.
            val end=System.nanoTime()+10_000_000_000L; var released=false
            while(!released && System.nanoTime()<end) { released=runCatching { ProductSession(context,root,approved,false).use { }; true }.getOrDefault(false); if(!released) android.os.SystemClock.sleep(50) }
            check(released); require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator)); root.deleteRecursively()
        }
    }
}
