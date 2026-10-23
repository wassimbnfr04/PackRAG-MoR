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

@RunWith(AndroidJUnit4::class)
class SourceDetailsPolicyTest {
    @Test fun productionInspectionCannotBypassMissingIdentityOrUnapprovedFixtureTrust() {
        assertFalse(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext
        val root=File(context.filesDir,"source-detail-policy-${UUID.randomUUID()}");val store=ViewModelStore()
        val input=File(context.cacheDir,"source-detail-policy-${UUID.randomUUID()}.kpack")
        lateinit var model:PackRagViewModel;val cases=JSONArray()
        fun ready() { val end=System.nanoTime()+30_000_000_000L;while(model.state.value.busy && System.nanoTime()<end) android.os.SystemClock.sleep(20);assertFalse(model.state.value.busy) }
        try {
            instrument.runOnMainSync { model=PackRagViewModel(context.applicationContext as Application,root);store.put("model",model) };ready()
            instrument.runOnMainSync { model.inspectPack("org.packrag.contract.source-details","1.0.0","0".repeat(64)) };ready()
            assertEquals("PACK_DETAIL_VERIFICATION_FAILED",model.state.value.message);assertNull(model.state.value.details);assertNotNull(model.state.value.detailsError)
            assertTrue(model.state.value.packs.isEmpty());assertTrue(model.state.value.installed.isEmpty());assertNull(model.state.value.trace)
            cases.put(JSONObject().put("id","production-missing-inspection-no-verified-dto-or-activation").put("passed",true))
            instrument.context.assets.open("source-details-corpus/source-details.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }
            instrument.runOnMainSync { model.importPack(Uri.fromFile(input)) };ready()
            assertEquals("RUNTIME_ERROR",model.state.value.answer?.state);assertNull(model.state.value.details);assertNull(model.state.value.detailRequest)
            assertTrue(model.state.value.packs.isEmpty());assertTrue(model.state.value.installed.isEmpty())
            cases.put(JSONObject().put("id","production-app-rejects-new-unapproved-fixture-key").put("passed",true))
            File(context.filesDir,"m4-source-details-policy.json").writeText(JSONObject().put("status","PASS").put("cases",cases)
                .put("compiled_developer_mode",false).put("raw_reasoning_persisted",false).toString(2),Charsets.UTF_8)
        } finally {
            instrument.runOnMainSync { store.clear() };input.delete();val end=System.nanoTime()+10_000_000_000L;var released=false
            while(!released && System.nanoTime()<end) {
                released=runCatching { ProductSession(context,root,ProductConfiguration.keys(context),false).use { };true }.getOrDefault(false)
                if(!released) android.os.SystemClock.sleep(50)
            }
            check(released);require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));assertTrue(root.deleteRecursively())
        }
    }
}
