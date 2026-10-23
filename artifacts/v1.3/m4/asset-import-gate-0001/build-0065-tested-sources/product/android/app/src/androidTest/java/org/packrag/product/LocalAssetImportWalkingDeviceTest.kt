package org.packrag.product

import android.content.Context
import android.content.ContextWrapper
import android.net.Uri
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.SimpleFileVisitor
import java.nio.file.FileVisitResult
import java.nio.file.Path
import java.nio.file.attribute.BasicFileAttributes
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.model.Query
import org.packrag.runtime.RuntimeTrace

/** First API iteration: real separate-UID URI transport, private commit and native smoke. */
@RunWith(AndroidJUnit4::class)
class LocalAssetImportWalkingDeviceTest {
    private val instrumentation get()=InstrumentationRegistry.getInstrumentation()
    private val context get()=instrumentation.targetContext
    private val uri=Uri.parse("content://org.packrag.product.test.asset-fixtures/template-valid")
    private val query=Query("What is the maximum continuous operating temperature of the Aster-9?","2027-01-01",null,true)
    private class PrivateContext(base:Context,private val root:File):ContextWrapper(base){override fun getFilesDir()=root}
    private fun guards():Map<String,String> {
        val result=sortedMapOf<String,String>()
        for(name in listOf("packs","production-registry","models")) {
            val root=File(context.filesDir,name).toPath()
            if(!Files.exists(root,LinkOption.NOFOLLOW_LINKS)) continue
            Files.walkFileTree(root,object:SimpleFileVisitor<Path>() {
                override fun preVisitDirectory(dir:Path,attrs:BasicFileAttributes):FileVisitResult {
                    val label=dir.fileName.toString()
                    return if(label==".private" || label.contains("temp",true) || label in setOf("stage",".asset-import-v1")) FileVisitResult.SKIP_SUBTREE else FileVisitResult.CONTINUE
                }
                override fun visitFile(file:Path,attrs:BasicFileAttributes):FileVisitResult {
                    check(!attrs.isSymbolicLink);if(attrs.isRegularFile) result[file.toFile().relativeTo(context.filesDir).invariantSeparatorsPath]=Crypto.fileHash(file.toFile())
                    return FileVisitResult.CONTINUE
                }
            })
        }
        return result
    }
    private fun provider():JSONObject {
        return context.contentResolver.query(uri,null,null,null,null)!!.use { cursor ->
            assertTrue(cursor.moveToFirst());JSONObject().apply {for(name in listOf("opens","closes","close_errors","provider_uid"))put(name,cursor.getInt(cursor.getColumnIndexOrThrow(name)))}
        }
    }
    private fun grantAfterInstrumentationStarts():String {
        val descriptor=instrumentation.uiAutomation.executeShellCommand("am broadcast --user 0 -n org.packrag.product.test/org.packrag.product.AssetFixtureGrantReceiver -a org.packrag.product.test.GRANT_TEMPLATE")
        val output=android.os.ParcelFileDescriptor.AutoCloseInputStream(descriptor).bufferedReader().use{it.readText()}
        assertTrue(output.contains("result=1"));assertTrue(output.contains("NARROW_TEMPLATE_READ_GRANTED"));return output
    }
    private fun accepted(trace:RuntimeTrace) {
        assertEquals("ANSWER_ACCEPTED",trace.answer.state);assertTrue(trace.answer.text!!.contains("74 °C"));assertTrue(trace.answer.text!!.contains("[S1]"))
        assertFalse(trace.answer.text!!.contains("</think>"));assertFalse(trace.answer.text!!.contains("<think>"))
        assertEquals("266af80f5d4da1dac500acd9a2bcc1fd2317b2caf49141ebb586280b9df49333",trace.answer.sources.single().canonicalTextSha256)
        assertTrue(trace.diagnostics!!.generationCalled);assertEquals(query,trace.evidenceContext!!.query)
        assertTrue(trace.session!!.embedderInitialized);assertNotNull(trace.session!!.generator)
        assertTrue(trace.emittedTokens in 1..512);assertTrue(trace.initializationMs>0)
    }
    @Test fun grantedTemplateCommitClosesWarmModelsAndColdRealAnswerStillPasses() {
        val before=guards();val root=File(context.filesDir,"asset-import-walking-${UUID.randomUUID()}");assertTrue(root.mkdir())
        val cases=JSONArray();fun passed(id:String){cases.put(JSONObject().put("id",id).put("passed",true))}
        val privateContext=PrivateContext(context,root);val progress=mutableListOf<LocalAssetImportProgress>()
        try {
            val needed=LocalAssetSlot.entries.sumOf{it.expectedBytes}
            assertTrue(android.os.StatFs(root.absolutePath).availableBytes>=needed+64L*1024*1024)
            for(slot in LocalAssetSlot.entries) {
                val target=File(root,"models/${slot.relativePath}");check(target.parentFile!!.mkdirs() || target.parentFile!!.isDirectory)
                File(context.filesDir,"models/${slot.relativePath}").copyTo(target)
            }
            val input=File(root,"input.kpack")
            val fixture=if(BuildConfig.ALLOW_DEVELOPMENT_PACKS) "walking-skeleton.kpack" else "release-trust-corpus/calibration-schema-only.kpack"
            instrumentation.context.assets.open(fixture).use { source->input.outputStream().use { source.copyTo(it) } }
            assertEquals(if(BuildConfig.ALLOW_DEVELOPMENT_PACKS) "19da286b9f0860c312dc8d14ce0ee8681bf12ca092a7b8a12171fd86abe02c7f" else
                "eb1d477f32e60ce97784320994d473690dd97ff4d13b49d921c93aad82b58011",Crypto.fileHash(input))
            val grantOutput=grantAfterInstrumentationStarts()
            val auditBefore=provider();assertNotEquals(android.os.Process.myUid(),auditBefore.getInt("provider_uid"))
            passed("actual-narrow-read-grant-to-separate-provider-uid")
            ProductSession(privateContext,File(root,"registry"),ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS).use { session ->
                session.registry.activate(input);val first=session.ask(query);accepted(first)
                assertNotNull(session.generatorLoadAndVerificationMs);passed("actual-pinned-pre-import-native-walking-answer")
                ProductSession(privateContext,File(root,"foreign-registry"),ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS).use { foreign ->
                    assertThrows(LocalAssetsBusy::class.java){foreign.importLocalAsset(LocalAssetSlot.TEMPLATE,uri)}
                    assertEquals(auditBefore.getInt("opens"),provider().getInt("opens"))
                    assertEquals(LocalAssetSlot.TEMPLATE.expectedSha256,Crypto.fileHash(File(root,"models/chat_template.jinja")))
                }
                passed("actual-foreign-native-reader-rejects-import-before-provider-open-or-replacement")
                val result=session.importLocalAsset(LocalAssetSlot.TEMPLATE,uri){progress.add(it)}
                assertEquals(5443L,result.bytes);assertEquals(LocalAssetSlot.TEMPLATE.expectedSha256,result.sha256);assertTrue(result.directorySynced)
                assertEquals(result.sha256,Crypto.fileHash(File(root,"models/chat_template.jinja")))
                assertFalse(File(root,"models/.asset-import-v1").exists());assertNull(session.generatorLoadAndVerificationMs)
                val statuses=session.localAssetStatuses();assertEquals(LocalAssetCondition.VERIFIED,statuses.single{it.spec.slot==LocalAssetSlot.TEMPLATE}.condition)
                assertTrue(statuses.filter{it.spec.slot!=LocalAssetSlot.TEMPLATE}.all{it.condition==LocalAssetCondition.UNCHECKED})
                passed("actual-template-stream-private-readback-atomic-replacement-and-caller-native-release")
                assertEquals(LocalAssetImportStage.COMMITTED,progress.last().stage);assertEquals(5443L,progress.last().copiedBytes)
                assertEquals(listOf(LocalAssetImportStage.COPYING,LocalAssetImportStage.SYNCING,LocalAssetImportStage.VERIFYING,LocalAssetImportStage.COMMITTING,LocalAssetImportStage.COMMITTED),progress.map{it.stage}.distinct())
                assertTrue(progress.all{it.copiedBytes in 0..5443 && it.expectedBytes==5443L})
                passed("observed-bytes-and-commit-progress-contract")
                val end=System.nanoTime()+10_000_000_000L;var auditAfter=provider()
                while(auditAfter.getInt("closes")!=auditBefore.getInt("closes")+1 && System.nanoTime()<end){android.os.SystemClock.sleep(20);auditAfter=provider()}
                assertEquals(auditBefore.getInt("opens")+1,auditAfter.getInt("opens"));assertEquals(auditBefore.getInt("closes")+1,auditAfter.getInt("closes"))
                assertEquals(auditBefore.getInt("close_errors"),auditAfter.getInt("close_errors"));passed("one-actual-provider-descriptor-open-and-close-without-error")
                val after=session.ask(query);accepted(after);passed("actual-post-import-cold-native-retrieval-admission-selection-citation-answer")
                assertEquals(before,guards())
                File(context.filesDir,"m4-local-asset-import-walking.json").writeText(JSONObject().put("status","PASS").put("cases",cases)
                    .put("variant",BuildConfig.BUILD_TYPE).put("actual_weight_inference",true).put("provider_before",auditBefore).put("provider_after",auditAfter)
                    .put("transport","TEST_APK_SEPARATE_UID_EXPLICIT_SHELL_DUMP_PROTECTED_NARROW_GRANT_NOT_SYSTEM_PICKER")
                    .put("actual_grant_after_instrumentation_start",grantOutput)
                    .put("product_uid",android.os.Process.myUid()).put("import_bytes",result.bytes).put("import_sha256",result.sha256)
                    .put("completed_at",result.completedAt).put("directory_synced",result.directorySynced)
                    .put("progress",JSONArray(progress.map{JSONObject().put("slot",it.slot.name).put("stage",it.stage.name).put("copied_bytes",it.copiedBytes).put("expected_bytes",it.expectedBytes)}))
                    .put("answer_before",first.answer.text).put("answer_after",after.answer.text).put("initialization_ms_before",first.initializationMs).put("initialization_ms_after",after.initializationMs)
                    .put("emitted_tokens_before",first.emittedTokens).put("emitted_tokens_after",after.emittedTokens)
                    .put("owner_registry_and_model_sha256",JSONObject(before)).put("guards_unchanged",true).put("raw_reasoning_persisted",false)
                    .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET")
                    .put("limits","API walking iteration only. Not system picker, all-slot import, restart/fault/UI, full F2/M4/product, power-loss durability, domain/gold or performance acceptance.").toString(2),Charsets.UTF_8)
            }
        } finally {
            require(root.parentFile!!.canonicalFile==context.filesDir.canonicalFile)
            Files.walkFileTree(root.toPath(),object:SimpleFileVisitor<Path>(){
                override fun visitFile(file:Path,attrs:BasicFileAttributes):FileVisitResult{Files.delete(file);return FileVisitResult.CONTINUE}
                override fun postVisitDirectory(dir:Path,error:java.io.IOException?):FileVisitResult{if(error!=null)throw error;Files.delete(dir);return FileVisitResult.CONTINUE}
            })
        }
    }
}
