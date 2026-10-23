package org.packrag.product

import android.app.Application
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

/** Real compiled production configuration; no developer trust or alternate backend. */
@RunWith(AndroidJUnit4::class)
class QueryControlsPolicyTest {
    @Test fun productionControlsCaptureNoPackRejectInvalidInputAndRejectDeveloperPack() {
        assertFalse(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext
        val root=File(context.filesDir,"query-policy-${UUID.randomUUID()}");val store=ViewModelStore()
        val input=File(context.cacheDir,"query-policy-${UUID.randomUUID()}.kpack")
        lateinit var model:PackRagViewModel
        fun ready() { val end=System.nanoTime()+30_000_000_000L;while(model.state.value.busy && System.nanoTime()<end) android.os.SystemClock.sleep(20);assertFalse(model.state.value.busy) }
        val cases=JSONArray()
        try {
            instrument.runOnMainSync { model=PackRagViewModel(context.applicationContext as Application,root);store.put("test",model) };ready()
            instrument.runOnMainSync { model.ask("Policy question","2028-02-29","MA-01",true) };ready()
            assertEquals("NO_ACTIVE_PACK",model.state.value.answer?.state)
            val captured=requireNotNull(model.state.value.submission)
            assertEquals("2028-02-29",captured.query.asOf);assertEquals("MA-01",captured.query.jurisdiction);assertTrue(captured.query.currentLaw)
            assertEquals(0.0,model.state.value.trace!!.initializationMs,0.0)
            cases.put(JSONObject().put("id","production-no-pack-captures-controls-no-initialization").put("passed",true))
            instrument.runOnMainSync { model.ask("Policy question","2027-02-29") };ready()
            assertEquals("INVALID_QUERY",model.state.value.answer?.state);assertEquals("INVALID_QUERY_DATE",model.state.value.inputError)
            assertNull(model.state.value.trace);assertNull(model.state.value.submission)
            cases.put(JSONObject().put("id","production-invalid-date-clears-old-context").put("passed",true))
            instrument.context.assets.open("walking-skeleton.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
            instrument.runOnMainSync { model.importPack(Uri.fromFile(input)) };ready()
            assertEquals("RUNTIME_ERROR",model.state.value.answer?.state);assertTrue(model.state.value.packs.isEmpty());assertTrue(model.state.value.installed.isEmpty())
            assertNull(model.state.value.trace);assertNull(model.state.value.submission)
            cases.put(JSONObject().put("id","production-viewmodel-rejects-developer-signer").put("passed",true))
            File(context.filesDir,"m4-ui-query-policy.json").writeText(JSONObject().put("status","PASS").put("cases",cases)
                .put("compiled_developer_mode",false).put("limits","No-pack controls and developer-pack rejection under actual compiled policy; approved-signer real generation is the retained release-trust core gate.")
                .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET").toString(2),Charsets.UTF_8)
        } finally {
            instrument.runOnMainSync { store.clear() };input.delete();val end=System.nanoTime()+10_000_000_000L;var released=false
            while(!released && System.nanoTime()<end) {
                released=runCatching { ProductSession(context,root,ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS).use { };true }.getOrDefault(false)
                if(!released) android.os.SystemClock.sleep(50)
            }
            check(released);require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));root.deleteRecursively()
        }
    }
}
