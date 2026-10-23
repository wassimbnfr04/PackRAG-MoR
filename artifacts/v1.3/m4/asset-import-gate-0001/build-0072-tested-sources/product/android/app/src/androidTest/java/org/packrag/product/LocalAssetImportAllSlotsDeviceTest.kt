package org.packrag.product

import android.content.Context
import android.content.ContextWrapper
import android.net.Uri
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.Path
import java.nio.file.SimpleFileVisitor
import java.nio.file.FileVisitResult
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

/** Actual full pinned files cross a separate UID into an initially empty private model root. */
@RunWith(AndroidJUnit4::class)
class LocalAssetImportAllSlotsDeviceTest {
    private val instrument get()=InstrumentationRegistry.getInstrumentation()
    private val context get()=instrument.targetContext
    private class PrivateContext(base:Context,private val root:File):ContextWrapper(base){override fun getFilesDir()=root}
    private val query=Query("What is the maximum continuous operating temperature of the Aster-9?","2027-01-01",null,true)
    private fun guards():Map<String,String> {
        val expected=instrument.context.assets.open("asset-import-source/owner-public-baseline.json").bufferedReader().use{JSONObject(it.readText())}
        assertEquals(50,expected.length());val observed=sortedMapOf<String,String>()
        for(name in expected.keys()) {
            assertFalse(name.split('/').any{it in setOf(".private","..",".") || it.contains("keystore",true) || it.contains("seed",true)})
            assertTrue(name.startsWith("models/") || name.startsWith("packs/") || name.startsWith("production-registry/"))
            var path=context.filesDir.toPath()
            name.split('/').forEachIndexed { i,part ->
                path=path.resolve(part);val attrs=Files.readAttributes(path,BasicFileAttributes::class.java,LinkOption.NOFOLLOW_LINKS)
                assertFalse(attrs.isSymbolicLink);if(i<name.split('/').lastIndex)assertTrue(attrs.isDirectory) else assertTrue(attrs.isRegularFile)
            }
            observed[name]=Crypto.fileHash(path.toFile());assertEquals(name,expected.getString(name),observed[name])
        };return observed
    }
    private fun provider(uri:Uri):JSONObject=context.contentResolver.query(uri,null,null,null,null)!!.use { cursor ->
        assertTrue(cursor.moveToFirst());JSONObject().apply{for(name in listOf("opens","closes","close_errors","provider_uid","typed_cancellable_opens","typed_plain_opens"))put(name,cursor.getInt(cursor.getColumnIndexOrThrow(name)))}
    }
    private fun accepted(trace:RuntimeTrace,cold:Boolean) {
        assertEquals("ANSWER_ACCEPTED",trace.answer.state);assertTrue(trace.answer.text!!.contains("74 °C"));assertTrue(trace.answer.text!!.contains("[S1]"))
        assertFalse(trace.answer.text!!.contains("<think>"));assertFalse(trace.answer.text!!.contains("</think>"))
        assertEquals("266af80f5d4da1dac500acd9a2bcc1fd2317b2caf49141ebb586280b9df49333",trace.answer.sources.single().canonicalTextSha256)
        assertTrue(trace.diagnostics!!.generationCalled);assertEquals(query,trace.evidenceContext!!.query)
        assertNotNull(trace.session!!.generator);assertTrue(trace.emittedTokens in 1..512)
        if(cold){assertTrue(trace.initializationMs>0);assertTrue(trace.session!!.embedderInitialized)}
    }
    @Test fun allFourFullPinnedUriImportsThenActualColdAndWarmCitedAnswers() {
        val before=guards();val root=File(context.filesDir,"f2-allslot-${UUID.randomUUID()}")
        Files.createDirectory(root.toPath());val cases=JSONArray();val imports=JSONArray()
        val envelope=JSONObject().put("status","RUNNING").put("test_id",root.name).put("cases",cases).put("imports",imports).put("variant",BuildConfig.BUILD_TYPE)
        fun progress(point:String){File(context.filesDir,"m4-local-asset-import-all-slots-progress.json").writeText(envelope.put("current_point",point).toString(2),Charsets.UTF_8)}
        fun passed(id:String){cases.put(JSONObject().put("id",id).put("passed",true))}
        try {
            progress("PREPARING");val available=android.os.StatFs(root.absolutePath).availableBytes
            assertTrue(available>=LocalAssetSlot.entries.sumOf{it.expectedBytes}+64L*1024*1024)
            assertFalse(File(root,"models").exists())
            val descriptor=instrument.uiAutomation.executeShellCommand("am broadcast --user 0 -n org.packrag.product.test/org.packrag.product.AssetFixtureGrantReceiver -a org.packrag.product.test.GRANT_FULL_ASSETS")
            val grant=android.os.ParcelFileDescriptor.AutoCloseInputStream(descriptor).bufferedReader().use{it.readText()}
            assertTrue(grant.contains("result=1") && grant.contains("NARROW_FULL_ASSET_READS_GRANTED"))
            val auditUri=Uri.parse("content://org.packrag.product.test.asset-fixtures/full-template")
            val initial=provider(auditUri);assertNotEquals(android.os.Process.myUid(),initial.getInt("provider_uid"))
            passed("initially-missing-private-model-root-and-separate-uid-four-narrow-grants")
            ProductSession(PrivateContext(context,root),File(root,"registry"),ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS).use { session ->
                assertTrue(session.verifyLocalAssets().all{it.condition==LocalAssetCondition.MISSING})
                for(slot in LocalAssetSlot.entries) {
                    progress("IMPORT_${slot.name}");val stages=mutableListOf<LocalAssetImportStage>();var callbacks=0;var copied=0L
                    val start=System.nanoTime();val prior=provider(auditUri)
                    val uri=Uri.parse("content://org.packrag.product.test.asset-fixtures/full-${slot.name.lowercase()}")
                    val result=session.importLocalAsset(slot,uri){event ->
                        assertEquals(slot,event.slot);assertEquals(slot.expectedBytes,event.expectedBytes)
                        assertTrue(event.copiedBytes in copied..slot.expectedBytes);copied=event.copiedBytes;callbacks++
                        if(stages.lastOrNull()!=event.stage)stages.add(event.stage)
                    }
                    val duration=(System.nanoTime()-start)/1_000_000.0
                    assertEquals(slot.expectedBytes,result.bytes);assertEquals(slot.expectedSha256,result.sha256)
                    assertTrue(result.directorySynced);assertTrue(result.stagingCleaned);assertEquals(slot.expectedBytes,copied)
                    assertEquals(listOf(LocalAssetImportStage.COPYING,LocalAssetImportStage.SYNCING,LocalAssetImportStage.VERIFYING,LocalAssetImportStage.COMMITTING,LocalAssetImportStage.COMMITTED),stages)
                    val final=File(root,"models/${slot.relativePath}");assertEquals(slot.expectedBytes,final.length());assertEquals(slot.expectedSha256,Crypto.fileHash(final))
                    assertFalse(File(root,"models/.asset-import-v1").exists());assertNull(session.generatorLoadAndVerificationMs)
                    val statuses=session.localAssetStatuses();assertEquals(LocalAssetCondition.VERIFIED,statuses.single{it.spec.slot==slot}.condition)
                    assertTrue(statuses.filter{it.spec.slot!=slot}.all{it.condition==LocalAssetCondition.UNCHECKED})
                    val end=System.nanoTime()+10_000_000_000L;var after=provider(auditUri)
                    while(after.getInt("closes")!=prior.getInt("closes")+1 && System.nanoTime()<end){android.os.SystemClock.sleep(20);after=provider(auditUri)}
                    for(name in listOf("opens","closes","typed_cancellable_opens"))assertEquals(prior.getInt(name)+1,after.getInt(name))
                    for(name in listOf("close_errors","typed_plain_opens"))assertEquals(prior.getInt(name),after.getInt(name))
                    imports.put(JSONObject().put("slot",slot.name).put("bytes",result.bytes).put("sha256",result.sha256).put("completed_at",result.completedAt)
                        .put("directory_synced",result.directorySynced).put("staging_cleaned",result.stagingCleaned).put("duration_ms",duration)
                        .put("progress_callbacks",callbacks).put("observed_final_bytes",copied).put("stages",JSONArray(stages.map{it.name})).put("provider_before",prior).put("provider_after",after))
                    passed("actual-full-size-${slot.name}-uri-readback-commit-close")
                }
                progress("VERIFY_ALL_FOUR");val verified=session.verifyLocalAssets();assertTrue(verified.all{it.condition==LocalAssetCondition.VERIFIED})
                assertTrue(verified.all{it.observedBytes==it.spec.bytes && it.observedSha256==it.spec.sha256});passed("all-four-independent-pinned-final-file-verification")
                val input=File(root,"input.kpack");val fixture=if(BuildConfig.ALLOW_DEVELOPMENT_PACKS)"walking-skeleton.kpack" else "release-trust-corpus/calibration-schema-only.kpack"
                instrument.context.assets.open(fixture).use{source->input.outputStream().use{source.copyTo(it)}}
                assertEquals(if(BuildConfig.ALLOW_DEVELOPMENT_PACKS)"19da286b9f0860c312dc8d14ce0ee8681bf12ca092a7b8a12171fd86abe02c7f" else "eb1d477f32e60ce97784320994d473690dd97ff4d13b49d921c93aad82b58011",Crypto.fileHash(input))
                session.registry.activate(input);progress("COLD_NATIVE_ANSWER");val cold=session.ask(query);accepted(cold,true);passed("actual-cold-native-retrieval-admission-selection-citation-answer")
                progress("WARM_NATIVE_ANSWER");val warm=session.ask(query);accepted(warm,false);passed("actual-warm-native-retrieval-admission-selection-citation-answer")
                assertEquals(before,guards());envelope.put("owner_registry_and_model_sha256",JSONObject(before)).put("guards_unchanged",true)
                    .put("actual_weight_inference",true).put("raw_reasoning_persisted",false).put("grant_after_instrumentation_start",grant)
                    .put("product_uid",android.os.Process.myUid()).put("provider_initial",initial).put("provider_final",provider(auditUri)).put("available_bytes_before_target_import",available)
                    .put("answer_cold",cold.answer.text).put("answer_warm",warm.answer.text).put("emitted_tokens_cold",cold.emittedTokens).put("emitted_tokens_warm",warm.emittedTokens)
                    .put("initialization_ms_cold",cold.initializationMs).put("initialization_ms_warm",warm.initializationMs)
                    .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET")
                    .put("limits","Actual four-slot full-size separate-UID explicit-grant API transport/native smoke. Not system picker, ViewModel/UI, physical power loss, final F2/M4/product or performance/gold/domain acceptance. Source hashes validated independently by host before and after; source set deliberately retained for later approved-policy/UI tests.")
                progress("COMPLETED");envelope.put("status","PASS")
                File(context.filesDir,"m4-local-asset-import-all-slots.json").writeText(envelope.toString(2),Charsets.UTF_8);progress("COMPLETED")
            }
        } catch(failure:Throwable){envelope.put("failure_type",failure.javaClass.simpleName).put("status","FAIL");File(context.filesDir,"m4-local-asset-import-all-slots-progress.json").writeText(envelope.toString(2),Charsets.UTF_8);throw failure}
        finally {
            require(root.parentFile!!.canonicalFile==context.filesDir.canonicalFile && root.name.matches(Regex("f2-allslot-[0-9a-f-]{36}")))
            Files.walkFileTree(root.toPath(),object:SimpleFileVisitor<Path>(){
                override fun preVisitDirectory(dir:Path,attrs:BasicFileAttributes):FileVisitResult{check(dir.fileName.toString()!=".private");return FileVisitResult.CONTINUE}
                override fun visitFile(file:Path,attrs:BasicFileAttributes):FileVisitResult{Files.delete(file);return FileVisitResult.CONTINUE}
                override fun postVisitDirectory(dir:Path,error:java.io.IOException?):FileVisitResult{if(error!=null)throw error;Files.delete(dir);return FileVisitResult.CONTINUE}
            })
        }
    }
}
