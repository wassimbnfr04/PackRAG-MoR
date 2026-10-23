package org.packrag.product

import android.net.Uri
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import java.io.File
import java.nio.file.Files
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto

/** Production ViewModel serialized import, observed cancellation and actual native result preservation. */
@RunWith(AndroidJUnit4::class)
class LocalAssetImportViewModelDeviceTest {
    @Test fun actualCompletedResultSurvivesImportFailureCancellationAndSuccessThenColdAnswerWorks() {
        assertTrue(BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val support=LocalAssetImportTestSupport;val instrument=support.instrument;val context=support.context
        val before=support.ownerGuard();val root=File(context.filesDir,"f2-import-model-${UUID.randomUUID()}");Files.createDirectory(root.toPath())
        val app=AssetImportPrivateApplication(context,root);val registry=File(root,"registry");val store=ViewModelStore()
        val cases=JSONArray();val envelope=JSONObject().put("status","RUNNING").put("test_id",root.name).put("cases",cases)
        lateinit var model:PackRagViewModel
        fun progress(point:String){File(context.filesDir,"m4-local-asset-import-viewmodel-progress.json").writeText(envelope.put("current_point",point).toString(2),Charsets.UTF_8)}
        fun waitUntil(timeoutMs:Long=600_000,condition:()->Boolean){val end=System.nanoTime()+timeoutMs*1_000_000;while(!condition() && System.nanoTime()<end)android.os.SystemClock.sleep(10);assertTrue(condition())}
        fun ready(timeoutMs:Long=600_000){waitUntil(timeoutMs){!model.state.value.busy};assertNotEquals("RUNTIME_ERROR",model.state.value.answer?.state);assertNull(model.state.value.localAssetImport)}
        fun passed(id:String){cases.put(JSONObject().put("id",id).put("passed",true))}
        fun uri(name:String)=Uri.parse("content://org.packrag.product.test.asset-fixtures/$name")
        try {
            progress("PREPARING");assertTrue(android.os.StatFs(root.absolutePath).availableBytes>=LocalAssetSlot.entries.sumOf{it.expectedBytes}+64L*1024*1024)
            envelope.put("grant_full",support.grant("GRANT_FULL_ASSETS")).put("grant_faults",support.grant("GRANT_CASES"))
            ProductSession(app,registry,ProductConfiguration.keys(context),true).use { session ->
                for(slot in LocalAssetSlot.entries)session.importLocalAsset(slot,uri("full-${slot.name.lowercase()}"))
                val input=File(root,"input.kpack");instrument.context.assets.open("walking-skeleton.kpack").use{source->input.outputStream().use{source.copyTo(it)}}
                assertEquals("19da286b9f0860c312dc8d14ce0ee8681bf12ca092a7b8a12171fd86abe02c7f",Crypto.fileHash(input))
                session.registry.activate(input)
            }
            instrument.runOnMainSync{model=PackRagViewModel(app,registry);store.put("isolated",model)};ready()
            progress("FIRST_REAL_VIEWMODEL_ANSWER")
            instrument.runOnMainSync{model.ask("What is the maximum continuous operating temperature of the Aster-9?","2027-01-01","",true)};ready()
            val completed=model.state.value;val firstAnswer=requireNotNull(completed.answer);val firstText=requireNotNull(firstAnswer.text);val firstTrace=requireNotNull(completed.trace)
            assertEquals("ANSWER_ACCEPTED",firstAnswer.state);assertTrue(firstText.contains("74 °C"));assertTrue(firstText.contains("[S1]"))
            assertTrue(firstTrace.diagnostics!!.generationCalled);assertTrue(firstTrace.emittedTokens in 1..512);assertNotNull(completed.completedResultId)
            fun preserved(){assertSame(completed.answer,model.state.value.answer);assertSame(completed.trace,model.state.value.trace);assertSame(completed.submission,model.state.value.submission);assertEquals(completed.completedResultId,model.state.value.completedResultId)
                assertEquals(LocalAssetSlot.TEMPLATE.expectedSha256,Crypto.fileHash(File(root,"models/chat_template.jinja")));assertFalse(File(root,"models/.asset-import-v1").exists())}
            passed("actual-native-completed-answer-and-owned-result-context")
            progress("WRONG_HASH")
            instrument.runOnMainSync{model.importLocalAsset(LocalAssetSlot.TEMPLATE,uri("corrupt"))};ready();preserved();assertTrue(model.state.value.message.contains("LOCAL_ASSET_IMPORT_HASH_MISMATCH"))
            passed("wrong-hash-rejection-preserves-file-answer-trace-submission-and-result-id")
            progress("NON_CONTENT_URI")
            instrument.runOnMainSync{model.importLocalAsset(LocalAssetSlot.TEMPLATE,Uri.parse("file:///not-an-admitted-source"))};ready();preserved()
            assertEquals("LOCAL_ASSET_CONTENT_URI_REQUIRED",model.state.value.message)
            passed("generic-source-rejection-recovery-preserves-owned-completion")
            progress("BLOCKED_READING_CANCEL")
            instrument.runOnMainSync{model.importLocalAsset(LocalAssetSlot.TEMPLATE,uri("blocked-pipe"))}
            waitUntil(15_000){model.state.value.localAssetImport?.copiedBytes==128L}
            val observed=model.state.value.localAssetImport!!;assertEquals(LocalAssetImportStage.COPYING,observed.stage);assertEquals(5443L,observed.expectedBytes);assertTrue(model.state.value.busy)
            val start=System.nanoTime();instrument.runOnMainSync{model.cancelLocalAssetImport()};val readingCancelMs=(System.nanoTime()-start)/1_000_000.0
            assertTrue(readingCancelMs<1000);ready(15_000);preserved();assertTrue(model.state.value.message.contains("cancelled"))
            envelope.put("observed_partial_copy_bytes",observed.copiedBytes).put("reading_cancel_dispatch_ms",readingCancelMs)
            passed("actual-observed-partial-byte-progress-and-cooperative-read-cancel-preserve-completion")
            progress("BLOCKED_OPENING_CANCEL");val initial=support.provider()
            instrument.runOnMainSync{model.importLocalAsset(LocalAssetSlot.TEMPLATE,uri("opening-blocked"))}
            waitUntil(15_000){support.provider().getInt("opening_attempts")==initial.getInt("opening_attempts")+1}
            val openingStart=System.nanoTime();instrument.runOnMainSync{model.cancelLocalAssetImport()};val openingCancelMs=(System.nanoTime()-openingStart)/1_000_000.0
            assertTrue(openingCancelMs<1000);ready(15_000);preserved();assertEquals(initial.getInt("opening_cancelled")+1,support.provider().getInt("opening_cancelled"))
            envelope.put("opening_cancel_dispatch_ms",openingCancelMs);passed("actual-transported-open-cancel-awaits-cleanup-and-preserves-completion")
            progress("VALID_TEMPLATE_IMPORT")
            instrument.runOnMainSync{model.importLocalAsset(LocalAssetSlot.TEMPLATE,uri("full-template"))};ready();preserved()
            assertTrue(model.state.value.message.contains("installed and verified"));assertEquals(LocalAssetCondition.VERIFIED,model.state.value.localAssets.single{it.spec.slot==LocalAssetSlot.TEMPLATE}.condition)
            assertTrue(model.state.value.localAssets.filter{it.spec.slot!=LocalAssetSlot.TEMPLATE}.all{it.condition==LocalAssetCondition.UNCHECKED})
            passed("successful-verified-import-preserves-completion-and-invalidates-other-cached-asset-checks")
            instrument.runOnMainSync{model.checkLocalAssets()};ready();preserved();assertTrue(model.state.value.localAssets.all{it.condition==LocalAssetCondition.VERIFIED})
            passed("independent-four-pin-recheck-preserves-completed-result")
            progress("POST_IMPORT_REAL_VIEWMODEL_ANSWER")
            instrument.runOnMainSync{model.ask("What is the maximum continuous operating temperature of the Aster-9?","2027-01-01","",true)};ready()
            val after=model.state.value;val afterAnswer=requireNotNull(after.answer);val afterText=requireNotNull(afterAnswer.text);val afterTrace=requireNotNull(after.trace)
            assertEquals("ANSWER_ACCEPTED",afterAnswer.state);assertTrue(afterText.contains("74 °C"));assertTrue(afterText.contains("[S1]"));assertNotEquals(completed.completedResultId,after.completedResultId)
            assertTrue(afterTrace.initializationMs>0);assertTrue(afterTrace.diagnostics!!.generationCalled);assertTrue(afterTrace.emittedTokens in 1..512)
            assertFalse(afterText.contains("<think>"));assertFalse(afterText.contains("</think>"));assertEquals("266af80f5d4da1dac500acd9a2bcc1fd2317b2caf49141ebb586280b9df49333",afterAnswer.sources.single().canonicalTextSha256)
            passed("actual-post-import-cold-native-answer-uses-new-owned-result-id")
            assertEquals(before,support.ownerGuard());envelope.put("status","PASS").put("variant",BuildConfig.BUILD_TYPE).put("owner_registry_and_model_sha256",JSONObject(before)).put("guards_unchanged",true)
                .put("actual_weight_inference",true).put("raw_reasoning_persisted",false).put("answer_before",firstText).put("answer_after",afterText)
                .put("emitted_tokens_before",firstTrace.emittedTokens).put("emitted_tokens_after",afterTrace.emittedTokens).put("completed_result_id_before",completed.completedResultId).put("completed_result_id_after",after.completedResultId)
                .put("initialization_ms_after",afterTrace.initializationMs).put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET")
                .put("limits","Actual background production ViewModel/API/native preservation and cooperative fixtures; no Activity/system picker/UI, arbitrary provider IPC bound, full F2/M4/product or performance/gold/domain acceptance.")
            File(context.filesDir,"m4-local-asset-import-viewmodel.json").writeText(envelope.toString(2),Charsets.UTF_8);progress("COMPLETED")
        } catch(failure:Throwable){envelope.put("status","FAIL").put("failure_type",failure.javaClass.simpleName);File(context.filesDir,"m4-local-asset-import-viewmodel-progress.json").writeText(envelope.toString(2),Charsets.UTF_8);throw failure}
        finally {
            instrument.runOnMainSync{store.clear()}
            var released=false;val end=System.nanoTime()+15_000_000_000L
            while(!released && System.nanoTime()<end){released=runCatching{ProductSession(app,registry,ProductConfiguration.keys(context),true).use{};true}.getOrDefault(false);if(!released)android.os.SystemClock.sleep(20)}
            check(released);support.deleteOwned(root,"f2-import-model-")
        }
    }
}
