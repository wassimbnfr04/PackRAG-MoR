package org.packrag.product

import android.os.ParcelFileDescriptor
import android.net.Uri
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.v2.createEmptyComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.packs.PackImportStage
import org.packrag.packs.PackImportState

/** Actual pinned ARM generator/ONNX through the new chat on an owned emulator.
 * No claim of physical Samsung throughput or broad repair competence.
 */
@RunWith(AndroidJUnit4::class)
class EmulatorChatRepairUiTest {
    @get:Rule val compose=createEmptyComposeRule()
    private val support get()=ProductUiTestSupport
    private fun guard():Map<String,String> {
        val fd=support.instrument.uiAutomation.executeShellCommand("getprop ro.kernel.qemu")
        assertEquals("1",ParcelFileDescriptor.AutoCloseInputStream(fd).bufferedReader().use{it.readText().trim()})
        for(name in listOf("packs","production-registry"))assertFalse(File(support.context.filesDir,name).exists())
        val observed=sortedMapOf<String,String>()
        for(slot in LocalAssetSlot.entries) {
            var path=File(support.context.filesDir,"models").toPath()
            assertTrue(Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS));assertFalse(Files.isSymbolicLink(path))
            slot.relativePath.split('/').forEach{path=path.resolve(it);assertFalse(Files.isSymbolicLink(path))}
            assertTrue(Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS));assertEquals(slot.expectedBytes,Files.size(path))
            assertEquals(slot.expectedSha256,Crypto.fileHash(path.toFile()));observed["models/"+slot.relativePath]=slot.expectedSha256
        }
        val pack=File(support.context.filesDir,"m4-repair-fixture-0001.kpack")
        assertTrue(Files.isRegularFile(pack.toPath(),LinkOption.NOFOLLOW_LINKS));assertFalse(Files.isSymbolicLink(pack.toPath()))
        assertEquals("c202956eb0554fecc439944ebf4d69b831ad4fa262ea1693d4ec7f00e0952359",Crypto.fileHash(pack))
        observed[pack.name]=Crypto.fileHash(pack);return observed
    }
    @Test fun actualRepairChatCapturesEvidenceAndRejectsPartialGuide() {
        val before=guard();val observations=JSONArray();val images=JSONObject()
        val output=File(support.context.filesDir,"m4-emulator-chat-repair.json")
        fun save(status:String)=output.writeText(JSONObject().put("status",status).put("environment","OWNED_EMULATOR_ARM64_NATIVE_BRIDGE")
            .put("observations",observations).put("visual_png",images).put("owner_guard_scope","FOUR_PINNED_EMULATOR_MODELS_ONE_FROZEN_FIXTURE_DEFAULT_REGISTRIES_ABSENT")
            .put("sha256_before",JSONObject(before)).put("raw_reasoning_persisted",false).put("phone_performance",false).toString(2),Charsets.UTF_8)
        save("STARTED_NOT_PASS")
        support.activity { scenario,model ->
            support.ready(compose,model)
            fun click(tag:String){compose.onNodeWithTag(tag).performScrollTo().performClick()}
            fun ask(id:String,question:String,expected:String):UiState {
                compose.onNodeWithTag("query-question").performTextReplacement(question);support.hideKeyboard(scenario)
                val previous=model.state.value.completedResultId;click("query-submit")
                compose.waitUntil(900_000){!model.state.value.busy && model.state.value.completedResultId!=null && model.state.value.completedResultId!=previous}
                support.ready(compose,model);val result=model.state.value;val trace=requireNotNull(result.trace)
                observations.put(JSONObject().put("id",id).put("question",question).put("expected",expected).put("actual",result.answer?.state)
                    .put("final_text",result.answer?.text ?: JSONObject.NULL).put("emitted_tokens",trace.emittedTokens)
                    .put("result_id",result.completedResultId).put("sources",JSONArray(result.answer!!.sources.map{source->JSONObject()
                        .put("evidence_id",source.evidenceId).put("canonical_sha256",source.canonicalTextSha256).put("manifest_sha256",source.pack.manifestSha256)})))
                save("OBSERVED_NOT_PASS")
                assertEquals(expected,result.answer?.state);assertFalse(result.answer?.text?.contains("</think>")==true)
                return result
            }
            val question="After taking the bicycle inner tube out, what must I inspect and how should I reinstall and inflate the replacement?"
            val noPack=ask("same-repair-before-import",question,"NO_ACTIVE_PACK");assertEquals(0,noPack.trace!!.emittedTokens)
            model.importPack(Uri.fromFile(File(support.context.filesDir,"m4-repair-fixture-0001.kpack")))
            support.ready(compose,model)
            assertEquals(1,model.state.value.packs.size)
            assertEquals(PackImportStage.entries.toList(),model.state.value.packImportEvents.map{it.stage})
            assertTrue(model.state.value.packImportEvents.all{it.state==PackImportState.PASSED})
            click("query-controls-toggle");compose.onNodeWithTag("query-date").performScrollTo().performTextReplacement("2026-10-12")
            support.hideKeyboard(scenario);click("query-controls-toggle")
            val accepted=ask("same-repair-after-verified-import",question,"ANSWER_ACCEPTED")
            assertTrue(accepted.trace!!.emittedTokens in 1..512)
            val source=accepted.answer!!.sources.single();val resultId=requireNotNull(accepted.completedResultId)
            assertEquals("4eea33f8f4a1ce9e319d9298d8b4adc5b30eefc3142d25e36fe20152a1f381c2",source.canonicalTextSha256)
            assertEquals("5cc28d05fe7a41ce0c258c8acbd5eecadd160bffd7f7ec257bfd443a817074da",source.pack.manifestSha256)
            click("source-$resultId-${source.evidenceId}")
            compose.onNodeWithTag("source-canonical-text").performScrollTo().assertTextEquals(source.canonicalText).assertIsDisplayed()
            images.put("m4-emulator-repair-source.png",support.screenshot(compose,"m4-emulator-repair-source.png"))
            click("source-back-answer")
            compose.onNodeWithTag("assistant-$resultId").performScrollTo().assertIsDisplayed()
            images.put("m4-emulator-repair-answer.png",support.screenshot(compose,"m4-emulator-repair-answer.png"))
            click("app-menu");click("diagnostics-toggle")
            support.instrument.sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_BACK)
            compose.onNodeWithTag("completed-diagnostics").performScrollTo().assertIsDisplayed()
            images.put("m4-emulator-repair-diagnostics.png",support.screenshot(compose,"m4-emulator-repair-diagnostics.png"))
            val partial=ask("long-guide-cap-fails-closed","My Framework Laptop 12 fan is dirty and noisy. How do I remove, clean, and reinstall it? Give an ordered guide including preparation and reassembly.","GENERATION_UNUSABLE")
            assertEquals(512,partial.trace!!.emittedTokens);assertNull(partial.answer!!.text);assertTrue(partial.answer.sources.isEmpty())
            val absent=ask("undocumented-inflation-abstention","What exact PSI should I inflate this bicycle inner tube to?","INSUFFICIENT_EVIDENCE")
            assertNull(absent.answer!!.text);assertTrue(absent.answer.sources.isEmpty())
            // An older S1 still opens its original result after later completions.
            click("source-$resultId-${source.evidenceId}")
            compose.onNodeWithTag("source-canonical-text").performScrollTo().assertTextEquals(source.canonicalText)
            click("source-back-answer");scenario.recreate();support.awaitForeground(scenario);support.ready(compose,model)
            assertEquals(4,model.turns.value.size);assertEquals(resultId,model.turns.value[1].resultId)
            click("manage-packs");val row=model.state.value.installed.single();click("deactivate-${row.tag}");support.ready(compose,model)
            click("packs-back-answer");val inactive=ask("same-repair-after-deactivation",question,"NO_ACTIVE_PACK");assertEquals(0,inactive.trace!!.emittedTokens)
            click("new-chat");assertTrue(model.turns.value.isEmpty());assertNull(model.state.value.completedResultId)
            save("FUNCTIONAL_ASSERTIONS_PASSED_GUARD_AND_MANUAL_REVIEW_PENDING")
        }
        assertEquals(before,guard());save("PASS_EXECUTION_ORIGINAL_FINAL_AND_PNG_REVIEW_REQUIRED")
    }
}
