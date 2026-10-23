package org.packrag.product

import android.content.Context
import android.content.ContextWrapper
import android.net.Uri
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.io.IOException
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.Path
import java.nio.file.SimpleFileVisitor
import java.nio.file.FileVisitResult
import java.nio.file.attribute.BasicFileAttributes
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.ExecutionException
import java.util.concurrent.TimeUnit
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto

/** Real grants/descriptors/Android filesystem; no owner model replacements or native mocks. */
@RunWith(AndroidJUnit4::class)
class LocalAssetImportFaultDeviceTest {
    private val instrument get()=InstrumentationRegistry.getInstrumentation()
    private val context get()=instrument.targetContext
    private class PrivateContext(base:Context,private val root:File):ContextWrapper(base){override fun getFilesDir()=root}
    private fun uri(name:String)=Uri.parse("content://org.packrag.product.test.asset-fixtures/$name")
    private fun broadcast(action:String):String {
        val descriptor=instrument.uiAutomation.executeShellCommand("am broadcast --user 0 -n org.packrag.product.test/org.packrag.product.AssetFixtureGrantReceiver -a org.packrag.product.test.$action")
        val out=android.os.ParcelFileDescriptor.AutoCloseInputStream(descriptor).bufferedReader().use{it.readText()}
        assertTrue(out.contains("result=1"));return out
    }
    private fun audit():JSONObject=context.contentResolver.query(uri("template-valid"),null,null,null,null)!!.use { cursor->
        assertTrue(cursor.moveToFirst());JSONObject().apply {
            for(name in listOf("opens","closes","close_errors","provider_uid","opening_attempts","opening_cancelled","pipe_writers_closed"))put(name,cursor.getInt(cursor.getColumnIndexOrThrow(name)))
        }
    }
    private fun guards():Map<String,String> {
        val values=sortedMapOf<String,String>()
        for(name in listOf("packs","production-registry","models")) {
            val folder=File(context.filesDir,name).toPath();if(!Files.exists(folder,LinkOption.NOFOLLOW_LINKS))continue
            Files.walkFileTree(folder,object:SimpleFileVisitor<Path>() {
                override fun preVisitDirectory(dir:Path,attrs:BasicFileAttributes):FileVisitResult {
                    val label=dir.fileName.toString();return if(label==".private" || label.contains("temp",true) || label in setOf("stage",".asset-import-v1"))FileVisitResult.SKIP_SUBTREE else FileVisitResult.CONTINUE
                }
                override fun visitFile(file:Path,attrs:BasicFileAttributes):FileVisitResult {
                    check(!attrs.isSymbolicLink);if(attrs.isRegularFile)values[file.toFile().relativeTo(context.filesDir).invariantSeparatorsPath]=Crypto.fileHash(file.toFile());return FileVisitResult.CONTINUE
                }
            })
        };return values
    }
    private fun owned(action:(File,Map<String,String>)->Unit) {
        val before=guards();val root=File(context.filesDir,"asset-import-fault-${UUID.randomUUID()}");assertTrue(root.mkdir())
        try{action(root,before);assertEquals(before,guards())}finally {
            require(root.parentFile!!.canonicalFile==context.filesDir.canonicalFile)
            Files.walkFileTree(root.toPath(),object:SimpleFileVisitor<Path>(){
                override fun visitFile(file:Path,attrs:BasicFileAttributes):FileVisitResult{Files.delete(file);return FileVisitResult.CONTINUE}
                override fun postVisitDirectory(dir:Path,error:IOException?):FileVisitResult{if(error!=null)throw error;Files.delete(dir);return FileVisitResult.CONTINUE}
            })
        }
    }
    private fun session(root:File)=ProductSession(PrivateContext(context,root),File(root,"registry"),ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS)
    private fun seedTemplate(root:File):File {
        val file=File(root,"models/chat_template.jinja");check(file.parentFile!!.mkdirs() || file.parentFile!!.isDirectory)
        File(context.filesDir,"models/chat_template.jinja").copyTo(file);return file
    }
    private fun unchanged(root:File,file:File) {
        assertEquals(LocalAssetSlot.TEMPLATE.expectedSha256,Crypto.fileHash(file));assertEquals(5443L,file.length())
        assertFalse(Files.exists(File(root,"models/.asset-import-v1").toPath(),LinkOption.NOFOLLOW_LINKS))
    }
    private fun record(name:String,cases:JSONArray,before:Map<String,String>,extra:JSONObject=JSONObject()) {
        assertEquals(before,guards())
        File(context.filesDir,name).writeText(extra.put("status","PASS").put("cases",cases).put("variant",BuildConfig.BUILD_TYPE)
            .put("owner_registry_and_model_sha256",JSONObject(before)).put("guards_unchanged",true).put("raw_reasoning_persisted",false)
            .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET")
            .put("limits","Real separate-UID test provider/explicit narrow grants and Android filesystem controls. No system-picker, all-slot/native, actual process-death, power-loss, full F2/M4/product or performance acceptance in these methods.").toString(2),Charsets.UTF_8)
    }
    @Test fun actualUriRejectionsMetadataShortStreamsAndCommitCancellationPreservePinnedFinal()=owned { root,before->
        assertTrue(broadcast("GRANT_CASES").contains("NARROW_FIXTURE_READS_GRANTED"))
        val file=seedTemplate(root);val cases=JSONArray();fun passed(id:String){cases.put(JSONObject().put("id",id).put("passed",true))}
        session(root).use { current->
            val initial=audit()
            val denied=assertThrows(LocalAssetImportFailed::class.java){current.importLocalAsset(LocalAssetSlot.TEMPLATE,uri("no-grant"))}
            assertEquals("LOCAL_ASSET_IMPORT_IO",denied.code);assertFalse(denied.cleanupPending);unchanged(root,file)
            assertEquals(initial.getInt("opens"),audit().getInt("opens"));passed("actual-ungranted-uri-rejects-without-provider-open-and-preserves-final")
            assertTrue(broadcast("REVOKE_CASES").contains("FIXTURE_READS_REVOKED"))
            val revoked=assertThrows(LocalAssetImportFailed::class.java){current.importLocalAsset(LocalAssetSlot.TEMPLATE,uri("template-valid"))}
            assertEquals("LOCAL_ASSET_IMPORT_IO",revoked.code);unchanged(root,file)
            broadcast("GRANT_CASES");assertEquals(initial.getInt("opens"),audit().getInt("opens"));passed("actual-revoked-before-open-grant-rejects-and-regrant-is-explicit")
            for(kind in listOf("empty","truncated","oversized","corrupt","read-error")) {
                val failure=assertThrows(LocalAssetImportFailed::class.java){current.importLocalAsset(LocalAssetSlot.TEMPLATE,uri(kind))}
                assertEquals(when(kind){"corrupt"->"LOCAL_ASSET_IMPORT_HASH_MISMATCH";"read-error"->"LOCAL_ASSET_IMPORT_IO";else->"LOCAL_ASSET_IMPORT_WRONG_SIZE"},failure.code)
                assertFalse(failure.cleanupPending);assertFalse(failure.message!!.contains("private provider error detail"));unchanged(root,file)
                assertNull(current.generatorLoadAndVerificationMs);passed("actual-$kind-uri-preserves-existing-pin-with-safe-error")
            }
            assertThrows(LocalAssetImportFailed::class.java){current.importLocalAsset(LocalAssetSlot.GENERATOR,uri("template-valid"))}
            unchanged(root,file);assertFalse(File(root,"models/${LocalAssetSlot.GENERATOR.relativePath}").exists());passed("actual-wrong-slot-template-source-cannot-install-generator")
            context.contentResolver.query(uri("metadata-lie"),null,null,null,null)!!.use{cursor->
                assertTrue(cursor.moveToFirst());assertEquals(Long.MAX_VALUE,cursor.getLong(cursor.getColumnIndexOrThrow("_size")))
                assertEquals("../../untrusted.gguf",cursor.getString(cursor.getColumnIndexOrThrow("_display_name")))
            }
            for(kind in listOf("metadata-lie","short-pipe")) {
                val result=current.importLocalAsset(LocalAssetSlot.TEMPLATE,uri(kind));assertEquals(5443L,result.bytes)
                assertEquals(LocalAssetSlot.TEMPLATE.expectedSha256,result.sha256);assertTrue(result.directorySynced);assertTrue(result.stagingCleaned);unchanged(root,file)
                passed("actual-$kind-uses-observed-stream-bytes-and-fixed-private-pin")
            }
            for(phase in listOf(LocalAssetImportStage.COPYING,LocalAssetImportStage.VERIFYING,LocalAssetImportStage.COMMITTING)) {
                val cancel=assertThrows(LocalAssetImportCancelled::class.java){current.importLocalAsset(LocalAssetSlot.TEMPLATE,uri("template-valid")){if(it.stage==phase)current.cancel()}}
                assertFalse(cancel.cleanupPending);unchanged(root,file);passed("actual-cancel-at-${phase.name}-is-precommit-and-preserves-pin")
            }
            val installed=current.importLocalAsset(LocalAssetSlot.TEMPLATE,uri("template-valid")){if(it.stage==LocalAssetImportStage.COMMITTED)current.cancel()}
            assertTrue(installed.directorySynced);assertTrue(installed.stagingCleaned);unchanged(root,file)
            assertEquals(LocalAssetCondition.VERIFIED,current.localAssetStatuses().single{it.spec.slot==LocalAssetSlot.TEMPLATE}.condition)
            passed("actual-late-cancel-does-not-report-committed-file-as-unchanged-failure")
            assertThrows(IllegalArgumentException::class.java){current.importLocalAsset(LocalAssetSlot.TEMPLATE,Uri.fromFile(file))}
            unchanged(root,file);passed("file-scheme-cannot-bypass-content-descriptor-interface")
        }
        record("m4-local-asset-import-uri-faults.json",cases,before,JSONObject().put("actual_narrow_grants",true))
    }
    @Test fun actualCancellableProviderOpeningAndBlockedPipeReadCloseBeforeRetry()=owned { root,before->
        broadcast("GRANT_CASES");val file=seedTemplate(root);val cases=JSONArray();val timings=JSONObject()
        val worker=Executors.newSingleThreadExecutor()
        try{session(root).use{current->
            val auditBefore=audit();val copied=CountDownLatch(1)
            val blocked=worker.submit<LocalAssetImportResult>{current.importLocalAsset(LocalAssetSlot.TEMPLATE,uri("blocked-pipe")){if(it.copiedBytes>0)copied.countDown()}}
            assertTrue(copied.await(10,TimeUnit.SECONDS));android.os.SystemClock.sleep(200);assertFalse(blocked.isDone)
            val start=System.nanoTime();instrument.runOnMainSync{current.cancel()};val mainMs=(System.nanoTime()-start)/1e6
            assertTrue("Cancel dispatch must not wait for provider IPC",mainMs<1000)
            val failure=assertThrows(ExecutionException::class.java){blocked.get(15,TimeUnit.SECONDS)};assertTrue(failure.cause is LocalAssetImportCancelled)
            assertFalse((failure.cause as LocalAssetImportCancelled).cleanupPending);unchanged(root,file)
            val pipeEnd=System.nanoTime()+15_000_000_000L;var after=audit()
            while(after.getInt("pipe_writers_closed")<auditBefore.getInt("pipe_writers_closed")+1 && System.nanoTime()<pipeEnd){android.os.SystemClock.sleep(20);after=audit()}
            assertEquals(auditBefore.getInt("pipe_writers_closed")+1,after.getInt("pipe_writers_closed"))
            cases.put(JSONObject().put("id","actual-blocked-pipe-read-cancel-closes-cooperative-producer-and-preserves-final").put("passed",true));timings.put("pipe_main_cancel_dispatch_ms",mainMs)
            val opening=worker.submit<LocalAssetImportResult>{current.importLocalAsset(LocalAssetSlot.TEMPLATE,uri("opening-blocked"))}
            val end=System.nanoTime()+10_000_000_000L;var observed=audit()
            while(observed.getInt("opening_attempts")==auditBefore.getInt("opening_attempts") && System.nanoTime()<end){android.os.SystemClock.sleep(20);observed=audit()}
            assertEquals(auditBefore.getInt("opening_attempts")+1,observed.getInt("opening_attempts"));assertFalse(opening.isDone)
            val openingStart=System.nanoTime();instrument.runOnMainSync{current.cancel()};val openingMainMs=(System.nanoTime()-openingStart)/1e6
            assertTrue(openingMainMs<1000)
            val openingFailure=assertThrows(ExecutionException::class.java){opening.get(15,TimeUnit.SECONDS)};assertTrue(openingFailure.cause is LocalAssetImportCancelled)
            assertFalse((openingFailure.cause as LocalAssetImportCancelled).cleanupPending);unchanged(root,file)
            assertEquals(auditBefore.getInt("opening_cancelled")+1,audit().getInt("opening_cancelled"))
            cases.put(JSONObject().put("id","actual-descriptor-opening-cancellation-signal-reaches-provider-without-blocking-main").put("passed",true));timings.put("opening_main_cancel_dispatch_ms",openingMainMs)
            val retry=current.importLocalAsset(LocalAssetSlot.TEMPLATE,uri("template-valid"));assertTrue(retry.stagingCleaned);unchanged(root,file)
            cases.put(JSONObject().put("id","actual-fresh-uri-retry-after-both-cancellations-commits-cleanly").put("passed",true))
        }}finally{worker.shutdown();assertTrue(worker.awaitTermination(20,TimeUnit.SECONDS))}
        record("m4-local-asset-import-provider-cancel.json",cases,before,JSONObject().put("timing_scope","Specific cooperative-provider cancellation dispatch/watchdogs, not hardware/performance benchmark or a bound for arbitrary uncooperative IPC").put("timings",timings))
    }
    @Test fun actualAndroidSymlinksOwnedStartupRecoveryAndSyncFaultNeverPromoteUnsafeStages()=owned { root,before->
        broadcast("GRANT_CASES");val file=seedTemplate(root);val models=file.parentFile!!;val staging=File(models,".asset-import-v1")
        val cases=JSONArray();fun passed(id:String){cases.put(JSONObject().put("id",id).put("passed",true))}
        val stageName="TEMPLATE-00000000-0000-0000-0000-000000000000.part"
        fun marker(){assertTrue(staging.mkdir());File(staging,"owner.marker").writeText("PackRAG owned asset import v1\n")}
        val legacy=File(models,"chat_template.jinja.part");legacy.writeText("legacy stays");marker();File(staging,stageName).writeText("incomplete")
        session(root).use{assertFalse(staging.exists());assertNull(it.generatorLoadAndVerificationMs)}
        unchanged(root,file);assertEquals("legacy stays",legacy.readText());passed("actual-new-session-reconciles-validated-abandoned-stage-without-promotion-or-legacy-deletion")
        marker();val stage=File(staging,stageName);stage.writeText("partial");val privateEntry=File(staging,".private");assertTrue(privateEntry.mkdir())
        assertThrows(LocalAssetImportFailed::class.java){session(root).use{}}
        assertEquals("partial",stage.readText());assertTrue(File(staging,"owner.marker").exists());assertTrue(privateEntry.exists())
        privateEntry.delete();stage.delete();File(staging,"owner.marker").delete();staging.delete();passed("unknown-private-named-entry-blocks-whole-startup-cleanup-without-traversal")
        val sentinel=File(root,"sentinel");sentinel.writeText("do not modify");val sentinelSha=Crypto.fileHash(sentinel)
        session(root).use{current->
            val opens=audit().getInt("opens");assertTrue(file.delete());Files.createSymbolicLink(file.toPath(),sentinel.toPath())
            assertThrows(LocalAssetImportFailed::class.java){current.importLocalAsset(LocalAssetSlot.TEMPLATE,uri("template-valid"))}
            assertEquals(opens,audit().getInt("opens"));assertEquals(sentinelSha,Crypto.fileHash(sentinel));Files.delete(file.toPath());File(context.filesDir,"models/chat_template.jinja").copyTo(file)
            passed("actual-final-leaf-symlink-rejects-before-source-open-and-never-follows-target")
            val granite=File(models,"granite");Files.createSymbolicLink(granite.toPath(),root.toPath())
            assertThrows(LocalAssetImportFailed::class.java){current.importLocalAsset(LocalAssetSlot.TOKENIZER,uri("template-valid"))}
            assertEquals(opens,audit().getInt("opens"));assertEquals(sentinelSha,Crypto.fileHash(sentinel));Files.delete(granite.toPath())
            passed("actual-nested-destination-parent-symlink-rejects-before-source-open")
        }
        marker();Files.delete(File(staging,"owner.marker").toPath());Files.createSymbolicLink(File(staging,"owner.marker").toPath(),sentinel.toPath())
        assertThrows(LocalAssetImportFailed::class.java){session(root).use{}}
        assertEquals(sentinelSha,Crypto.fileHash(sentinel));Files.delete(File(staging,"owner.marker").toPath());staging.delete();passed("actual-ownership-marker-symlink-rejected-without-reading-target")
        marker();Files.createSymbolicLink(File(staging,stageName).toPath(),sentinel.toPath())
        assertThrows(LocalAssetImportFailed::class.java){session(root).use{}}
        assertEquals(sentinelSha,Crypto.fileHash(sentinel));Files.delete(File(staging,stageName).toPath());File(staging,"owner.marker").delete();staging.delete();passed("actual-owned-stage-name-with-symlink-type-cannot-be-deleted-or-promoted")
        Files.createSymbolicLink(staging.toPath(),root.toPath());assertThrows(LocalAssetImportFailed::class.java){session(root).use{}}
        assertEquals(sentinelSha,Crypto.fileHash(sentinel));Files.delete(staging.toPath());passed("actual-staging-directory-symlink-cannot-trigger-recursive-cleanup")
        val linkedRoot=File(root,"model-root-link");Files.createSymbolicLink(linkedRoot.toPath(),models.toPath())
        assertThrows(LocalAssetImportFailed::class.java){LocalAssetImporter(linkedRoot,::syncLocalAssetDirectory).install(LocalAssetSlot.TEMPLATE,{throw AssertionError("must not open")})}
        assertEquals(sentinelSha,Crypto.fileHash(sentinel));unchanged(root,file);passed("actual-import-model-root-symlink-refuses-before-input")
        val injected=LocalAssetImporter(models,{throw IOException("controlled directory-sync fault")})
        val failure=assertThrows(LocalAssetImportFailed::class.java){injected.install(LocalAssetSlot.TEMPLATE,{throw AssertionError("sync failed before open")})}
        assertEquals("LOCAL_ASSET_IMPORT_IO",failure.code);assertTrue(failure.cleanupPending);assertEquals(LocalAssetSlot.TEMPLATE.expectedSha256,Crypto.fileHash(file))
        assertFalse(staging.exists());passed("controlled-precommit-directory-sync-fault-preserves-real-final-and-reports-unconfirmed-cleanup")
        session(root).use{assertEquals(LocalAssetCondition.VERIFIED,it.verifyLocalAssets().single{status->status.spec.slot==LocalAssetSlot.TEMPLATE}.condition)}
        assertEquals("legacy stays",legacy.readText());unchanged(root,file);passed("normal-new-session-recovers-after-injected-sync-fault-without-native-initialization")
        record("m4-local-asset-import-path-recovery.json",cases,before,JSONObject().put("recovery_scope","New session in same process and controlled exception injection, not actual process-death/power loss; separate crash-process gate still required"))
    }
}
