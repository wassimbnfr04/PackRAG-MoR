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
class PackImportConsentTest {
    @Test fun olderImportConsentBindsPrivateCopyAndCleansIt() {
        val instrument = InstrumentationRegistry.getInstrumentation(); val context = instrument.targetContext
        val root = File(context.filesDir,"m3-import-ui-${UUID.randomUUID()}")
        val input = File(context.cacheDir,"m3-import-source-${UUID.randomUUID()}.kpack")
        val store = ViewModelStore(); lateinit var model: PackRagViewModel
        val results = JSONArray()
        fun waitReady() {
            val end = System.nanoTime()+30_000_000_000L
            while(model.state.value.busy && System.nanoTime()<end) android.os.SystemClock.sleep(20)
            assertFalse("ViewModel operation timed out",model.state.value.busy)
        }
        fun action(block: () -> Unit) { instrument.runOnMainSync(block); waitReady() }
        fun seed(name: String) { instrument.context.assets.open("lifecycle-corpus/$name.kpack").use { source -> input.outputStream().use { source.copyTo(it) } } }
        fun imports() = context.cacheDir.listFiles()!!.filter { it.name.startsWith("import-") }.map { it.absolutePath }.toSet()
        val prior = imports()
        fun passed(name: String) { results.put(JSONObject().put("id",name).put("passed",true)) }
        try {
            instrument.runOnMainSync { model = PackRagViewModel(context.applicationContext as Application,root); store.put("test",model) }; waitReady()
            seed("v2"); action { model.importPack(Uri.fromFile(input)) }; assertNull(model.state.value.decision); assertEquals(listOf("1.0.1"),model.state.value.installed.map { it.version })
            seed("older"); action { model.importPack(Uri.fromFile(input)) }
            assertEquals("IMPORT_OLDER",model.state.value.decision?.kind); assertEquals("0.9.0",model.state.value.decision?.version)
            assertEquals(1,(imports()-prior).size); assertEquals(listOf("1.0.1"),model.state.value.installed.map { it.version })
            action { model.cancelDecision() }; assertEquals(prior,imports()); assertNull(model.state.value.decision); passed("older-import-awaits-consent-cancel-cleans-copy")
            action { model.importPack(Uri.fromFile(input)) }; seed("collision")
            action { model.confirmDecision() }; assertNull(model.state.value.decision); assertEquals("0.9.0",model.state.value.installed.single { it.active }.version)
            assertEquals(prior,imports()); passed("confirmed-import-uses-private-copy-not-mutated-caller-uri")
            seed("v1"); action { model.importPack(Uri.fromFile(input)) }; assertEquals("IMPORT_OLDER",model.state.value.decision?.kind)
            val pending = File((imports()-prior).single()); pending.appendBytes(byteArrayOf(0))
            action { model.confirmDecision() }; assertEquals("RUNTIME_ERROR",model.state.value.answer?.state)
            assertEquals("0.9.0",model.state.value.installed.single { it.active }.version); assertEquals(prior,imports()); passed("changed-private-copy-rejected-and-cleaned-prior-active-preserved")
            seed("v1"); action { model.importPack(Uri.fromFile(input)) }; assertEquals(1,(imports()-prior).size)
            instrument.runOnMainSync { store.clear() }
            val end = System.nanoTime()+10_000_000_000L
            while(imports()!=prior && System.nanoTime()<end) android.os.SystemClock.sleep(20)
            assertEquals(prior,imports()); passed("viewmodel-clear-cleans-pending-import")
            File(context.filesDir,"m3-import-consent.json").writeText(JSONObject().put("status","PASS").put("cases",results)
                .put("limits","Actual Android contentResolver file URI/private-copy lifecycle; SAF provider picker and visible consent dialog are separate UI gates.").toString(2),Charsets.UTF_8)
        } finally {
            instrument.runOnMainSync { store.clear() }; input.delete()
            require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator))
            // This test finishes after asynchronous onCleared cleanup above.
            android.os.SystemClock.sleep(100); root.deleteRecursively()
        }
    }
}
