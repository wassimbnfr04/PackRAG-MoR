package org.packrag.product

import android.content.Intent
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.v2.createEmptyComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
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
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier

@RunWith(AndroidJUnit4::class)
class PackManagementUiTest {
    @get:Rule val compose = createEmptyComposeRule()
    @Test fun isolatedPackControlsWarningsRemovalAndRestart() {
        val instrument = InstrumentationRegistry.getInstrumentation(); val context = instrument.targetContext
        val assets = instrument.context.assets
        val key = assets.open("lifecycle-corpus/public-key.raw").use { it.readBytes() }
        assertEquals(Crypto.sha256(key), Crypto.sha256(context.assets.open("lifecycle-public-key.raw").use { it.readBytes() }))
        val profile = assets.open("parity-reference.json").bufferedReader().use { JSONObject(it.readText()).getJSONObject("lock").getJSONObject("embedder").getJSONObject("pack_profile") }
        val schema = assets.open("schema.sql").bufferedReader().use { it.readText() }
        val verifier = PackVerifier(listOf(key),profile,schema,true)
        val testId = UUID.randomUUID().toString(); val root = File(context.filesDir,"ui-tests/$testId")
        val owner = File(context.filesDir,"packs")
        fun ownerHashes() = if(!owner.exists()) emptyMap<String,String>() else owner.walkTopDown().filter { it.isFile }.associate { it.relativeTo(owner).path to Crypto.fileHash(it) }
        val before = ownerHashes(); val results = JSONArray()
        val id = "org.packrag.development.walking-skeleton"
        fun tag(action: String, version: String) = "$action-$id@$version"
        fun click(tag: String) { compose.onNodeWithTag(tag).performScrollTo().performClick() }
        var scenario: ActivityScenario<MainActivity>? = null
        lateinit var model: PackRagViewModel
        fun settle() { compose.waitForIdle(); compose.waitUntil(30_000) { !model.state.value.busy }; assertNotEquals("RUNTIME_ERROR",model.state.value.answer?.state) }
        fun active(version: String?) { assertEquals(if(version==null) emptyList<String>() else listOf("$id@$version"),model.state.value.packs) }
        fun passed(name: String) { results.put(JSONObject().put("id",name).put("passed",true)) }
        try {
            PackRegistry(root,verifier).use { registry ->
                for(name in listOf("v1","v2")) {
                    val input = File(context.cacheDir,"ui-$testId-$name.kpack")
                    try { assets.open("lifecycle-corpus/$name.kpack").use { source -> input.outputStream().use { source.copyTo(it) } }; registry.activate(input) }
                    finally { input.delete() }
                }
            }
            fun launch() {
                scenario = ActivityScenario.launch(Intent(context,MainActivity::class.java).putExtra("packrag.debug.uiTestId",testId))
                scenario!!.onActivity { model = ViewModelProvider(it)[PackRagViewModel::class.java] }; settle()
            }
            launch(); active("1.0.1")
            compose.onNodeWithText("Manage packs").performScrollTo().performClick()
            click(tag("activate","1.0.0")); settle()
            compose.onNodeWithText("Older content").assertIsDisplayed(); active("1.0.1")
            compose.onNodeWithTag("cancel-pack-change").performClick(); settle(); active("1.0.1"); passed("older-activation-visible-warning-cancel-preserves-active")
            click(tag("rollback","1.0.1")); settle(); compose.onNodeWithText("Older content").assertIsDisplayed()
            compose.onNodeWithTag("confirm-pack-change").performClick(); settle(); active("1.0.0")
            assertEquals("1.0.1",model.state.value.installed.single { it.active }.newest); passed("deliberate-rollback-confirmation-keeps-newest-history")
            click(tag("activate","1.0.1")); settle(); active("1.0.1"); assertNull(model.state.value.decision)
            click(tag("deactivate","1.0.1")); settle(); active(null)
            click(tag("activate","1.0.1")); settle(); active("1.0.1"); passed("explicit-deactivate-and-reactivate-newest")
            click(tag("remove","1.0.1")); settle(); compose.onNodeWithText("Remove installed version?").assertIsDisplayed()
            compose.onNodeWithTag("cancel-pack-change").performClick(); settle(); active("1.0.1")
            click(tag("remove","1.0.1")); settle(); compose.onNodeWithTag("confirm-pack-change").performClick(); settle(); active(null)
            assertEquals(listOf("1.0.0"),model.state.value.installed.map { it.version }); passed("removal-cancel-and-confirm-no-automatic-fallback")
            compose.onNodeWithText("Back to answer").performScrollTo().performClick()
            compose.onNodeWithText("Question").performScrollTo().performTextInput("Aster-9 temperature limit?"); compose.onNodeWithText("Ask").performScrollTo().performClick(); settle()
            assertEquals("NO_ACTIVE_PACK",model.state.value.answer?.state); compose.onNodeWithText("NO_ACTIVE_PACK").assertIsDisplayed(); passed("all-inactive-no-pack-through-ui")
            scenario!!.recreate(); scenario!!.onActivity { model = ViewModelProvider(it)[PackRagViewModel::class.java] }; settle(); active(null)
            assertEquals(listOf("1.0.0"),model.state.value.installed.map { it.version }); passed("activity-recreation-retains-explicit-state")
            assertEquals(before,ownerHashes()); passed("owner-default-registry-all-file-hashes-unchanged")
            File(context.filesDir,"m3-pack-management-ui.json").writeText(JSONObject().put("status","PASS").put("cases",results)
                .put("isolated_registry",true).put("mobile_data_preserved",true)
                .put("limits","Synthetic lifecycle UI only; real LFM generation/source navigation and import-copy consent are separate tests. Recreation retains ViewModel, not process-death recovery.").toString(2),Charsets.UTF_8)
        } finally {
            scenario?.close()
            // onCleared closes on IO. Wait for the private root's exclusive lease.
            val end = System.nanoTime()+10_000_000_000L
            var released = false
            while(!released && System.nanoTime()<end) {
                released = runCatching { PackRegistry(root,verifier).use { }; true }.getOrDefault(false)
                if(!released) android.os.SystemClock.sleep(50)
            }
            check(released) { "UI registry lease was not released" }
            require(root.canonicalPath.startsWith(File(context.filesDir,"ui-tests").canonicalPath+File.separator)); root.deleteRecursively()
        }
    }
}
