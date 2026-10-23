package org.packrag.product

import android.content.ComponentName
import android.content.Context
import android.content.ContextWrapper
import android.content.Intent
import android.content.ServiceConnection
import android.os.IBinder
import android.os.Parcel
import android.os.DeadObjectException
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
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.model.Query
import org.packrag.runtime.RuntimeTrace

/** Actual importing subprocess death, then real startup and native recovery in one kernel. */
@RunWith(AndroidJUnit4::class)
class LocalAssetImportProcessDeathDeviceTest {
    private val instrument get()=InstrumentationRegistry.getInstrumentation()
    private val context get()=instrument.targetContext
    private class PrivateContext(base:Context,private val root:File):ContextWrapper(base){override fun getFilesDir()=root}
    private val query=Query("What is the maximum continuous operating temperature of the Aster-9?","2027-01-01",null,true)
    private fun guards():Map<String,String> {
        val result=sortedMapOf<String,String>()
        for(name in listOf("packs","production-registry","models")) {
            val folder=File(context.filesDir,name).toPath();if(!Files.exists(folder,LinkOption.NOFOLLOW_LINKS))continue
            Files.walkFileTree(folder,object:SimpleFileVisitor<Path>(){
                override fun preVisitDirectory(dir:Path,attrs:BasicFileAttributes):FileVisitResult {
                    val label=dir.fileName.toString();return if(label in setOf(".private","temp","stage","pytest-temp","host-temp","runner-temp") || Regex(".*-temp(-.*)?").matches(label))FileVisitResult.SKIP_SUBTREE else FileVisitResult.CONTINUE
                }
                override fun visitFile(file:Path,attrs:BasicFileAttributes):FileVisitResult {
                    check(!attrs.isSymbolicLink);if(attrs.isRegularFile)result[file.toFile().relativeTo(context.filesDir).invariantSeparatorsPath]=Crypto.fileHash(file.toFile());return FileVisitResult.CONTINUE
                }
            })
        };return result
    }
    private fun accepted(trace:RuntimeTrace) {
        assertEquals("ANSWER_ACCEPTED",trace.answer.state);assertTrue(trace.answer.text!!.contains("74 °C"));assertTrue(trace.answer.text!!.contains("[S1]"))
        assertFalse(trace.answer.text!!.contains("</think>"));assertFalse(trace.answer.text!!.contains("<think>"))
        assertEquals("266af80f5d4da1dac500acd9a2bcc1fd2317b2caf49141ebb586280b9df49333",trace.answer.sources.single().canonicalTextSha256)
        assertTrue(trace.diagnostics!!.generationCalled);assertEquals(query,trace.evidenceContext!!.query)
        assertTrue(trace.session!!.embedderInitialized);assertNotNull(trace.session!!.generator);assertTrue(trace.initializationMs>0);assertTrue(trace.emittedTokens in 1..512)
    }
    @Test fun actualImportingProcessLossAtCopyVerifiedRenameAndCommitRecoversRealCitedAnswers() {
        assertTrue(BuildConfig.DEBUG && BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val before=guards();val base=File(context.filesDir,"asset-import-crash")
        if(!Files.exists(base.toPath(),LinkOption.NOFOLLOW_LINKS))assertTrue(base.mkdir())
        val baseAttrs=Files.readAttributes(base.toPath(),BasicFileAttributes::class.java,LinkOption.NOFOLLOW_LINKS);assertTrue(baseAttrs.isDirectory && !baseAttrs.isSymbolicLink)
        val id=UUID.randomUUID().toString();val root=File(base,id);Files.createDirectory(root.toPath())
        val cases=JSONArray();var point="PREPARING";var lastProbePid:Int?=null
        val envelope=JSONObject().put("status","RUNNING").put("test_id",id).put("cases",cases)
        fun progress(state:String){File(context.filesDir,"m4-local-asset-import-process-death-progress.json").writeText(envelope.put("status",state).put("current_point",point).toString(2),Charsets.UTF_8)}
        fun session()=ProductSession(PrivateContext(context,root),File(root,"registry"),ProductConfiguration.keys(context),true)
        val uri=android.net.Uri.parse("content://org.packrag.product.test.asset-fixtures/template-valid")
        try {
            progress("RUNNING");File(root,"owned-probe-v1").outputStream().use{it.write("PackRAG F2 crash root v1\n".toByteArray(Charsets.US_ASCII));it.fd.sync()}
            syncLocalAssetDirectory(root.toPath())
            val needed=LocalAssetSlot.entries.filter{it!=LocalAssetSlot.TEMPLATE}.sumOf{it.expectedBytes}
            assertTrue(android.os.StatFs(root.absolutePath).availableBytes>=needed+64L*1024*1024)
            for(slot in LocalAssetSlot.entries.filter{it!=LocalAssetSlot.TEMPLATE}) {
                val target=File(root,"models/${slot.relativePath}");check(target.parentFile!!.mkdirs() || target.parentFile!!.isDirectory)
                File(context.filesDir,"models/${slot.relativePath}").copyTo(target)
            }
            val final=File(root,"models/chat_template.jinja");val legacy=File(root,"models/chat_template.jinja.part");legacy.writeText("legacy remains")
            val input=File(root,"input.kpack");instrument.context.assets.open("walking-skeleton.kpack").use{source->input.outputStream().use{source.copyTo(it)}}
            assertEquals("19da286b9f0860c312dc8d14ce0ee8681bf12ca092a7b8a12171fd86abe02c7f",Crypto.fileHash(input))
            session().use{it.registry.activate(input)}
            val descriptor=instrument.uiAutomation.executeShellCommand("am broadcast --user 0 -n org.packrag.product.test/org.packrag.product.AssetFixtureGrantReceiver -a org.packrag.product.test.GRANT_TEMPLATE")
            val grant=android.os.ParcelFileDescriptor.AutoCloseInputStream(descriptor).bufferedReader().use{it.readText()};assertTrue(grant.contains("result=1"))
            envelope.put("actual_narrow_grant",grant)
            val component=ComponentName(context.packageName,"org.packrag.product.AssetImportCrashProbeService")
            val info=context.packageManager.getServiceInfo(component,0);assertFalse(info.exported);assertEquals(context.packageName+":asset_import_crash_probe",info.processName)
            for(checkpoint in listOf(LocalAssetImportStage.COPYING,LocalAssetImportStage.COMMITTING,LocalAssetImportStage.COMMITTED)) {
                point=checkpoint.name;progress("RUNNING");final.writeText("older");val oldSha=Crypto.fileHash(final)
                val connected=CountDownLatch(1);val died=CountDownLatch(1);val bound=AtomicBoolean(false);var remote:IBinder?=null
                val connection=object:ServiceConnection {
                    override fun onServiceConnected(name:ComponentName,binder:IBinder){remote=binder;connected.countDown()}
                    override fun onServiceDisconnected(name:ComponentName){if(bound.compareAndSet(true,false))context.unbindService(this);died.countDown()}
                    override fun onBindingDied(name:ComponentName){if(bound.compareAndSet(true,false))context.unbindService(this);died.countDown()}
                    override fun onNullBinding(name:ComponentName){connected.countDown()}
                }
                bound.set(true)
                try {
                    assertTrue(context.bindService(Intent().setComponent(component).putExtra("test_id",id).putExtra("point",point),connection,Context.BIND_AUTO_CREATE))
                    assertTrue(connected.await(60,TimeUnit.SECONDS));val request=Parcel.obtain();val response=Parcel.obtain()
                    try {try{assertTrue(remote!!.transact(IBinder.FIRST_CALL_TRANSACTION,request,response,0));response.readException()}catch(dead:DeadObjectException){/* Real disconnect and synced status remain mandatory. */}}
                    finally{request.recycle();response.recycle()}
                    assertTrue("Importing probe did not die at $point",died.await(60,TimeUnit.SECONDS))
                }finally{if(bound.compareAndSet(true,false))context.unbindService(connection)}
                val probe=JSONObject(File(root,"probe-$point.json").readText(Charsets.UTF_8))
                assertEquals("KILLING",probe.getString("state"));assertEquals(point,probe.getString("point"));assertEquals(id,probe.getString("test_id"))
                assertNotEquals(android.os.Process.myPid(),probe.getInt("pid"));lastProbePid?.let{assertNotEquals(it,probe.getInt("pid"))};lastProbePid=probe.getInt("pid")
                assertEquals(5443L,probe.getLong("copied_bytes"))
                val namespace=File(root,"models/.asset-import-v1");val attrs=Files.readAttributes(namespace.toPath(),BasicFileAttributes::class.java,LinkOption.NOFOLLOW_LINKS)
                assertTrue(attrs.isDirectory && !attrs.isSymbolicLink)
                val staged=Files.newDirectoryStream(namespace.toPath()).use{stream->stream.filter{it.fileName.toString()!="owner.marker"}.toList()}
                val committed=checkpoint==LocalAssetImportStage.COMMITTED;assertEquals(if(committed)0 else 1,staged.size)
                var stageSha:String?=null
                for(path in staged) {
                    assertTrue(Regex("TEMPLATE-[0-9a-f-]{36}\\.part").matches(path.fileName.toString()))
                    val value=Files.readAttributes(path,BasicFileAttributes::class.java,LinkOption.NOFOLLOW_LINKS);assertTrue(value.isRegularFile && !value.isSymbolicLink);assertEquals(5443L,value.size())
                    stageSha=Crypto.fileHash(path.toFile());assertEquals(LocalAssetSlot.TEMPLATE.expectedSha256,stageSha)
                }
                assertEquals(if(committed)LocalAssetSlot.TEMPLATE.expectedSha256 else oldSha,Crypto.fileHash(final))
                val observed=JSONObject().put("id","actual-importing-process-death-$point").put("passed",false).put("probe",probe)
                    .put("namespace_existed_before_reopen",true).put("stage_count_before_reopen",staged.size).put("stage_sha256_before_reopen",stageSha ?: JSONObject.NULL)
                    .put("final_sha256_before_reopen",Crypto.fileHash(final)).put("commit_survived",committed)
                session().use{current->
                    assertFalse(namespace.exists());assertEquals("legacy remains",legacy.readText());assertNull(current.generatorLoadAndVerificationMs)
                    val statuses=current.verifyLocalAssets()
                    if(committed)assertTrue(statuses.all{it.condition==LocalAssetCondition.VERIFIED})
                    else {
                        assertEquals(oldSha,Crypto.fileHash(final));assertEquals(LocalAssetCondition.WRONG_SIZE,statuses.single{it.spec.slot==LocalAssetSlot.TEMPLATE}.condition)
                        assertThrows(LocalAssetsUnavailable::class.java){current.ask(query)};assertNull(current.generatorLoadAndVerificationMs)
                        val repair=current.importLocalAsset(LocalAssetSlot.TEMPLATE,uri);assertTrue(repair.directorySynced && repair.stagingCleaned)
                    }
                    val trace=current.ask(query);accepted(trace)
                    observed.put("answer",trace.answer.text).put("emitted_tokens",trace.emittedTokens).put("initialization_ms",trace.initializationMs)
                        .put("repair_import_required",!committed).put("fully_pinned_abandoned_stage_never_promoted",if(!committed)true else JSONObject.NULL)
                }
                assertEquals(LocalAssetSlot.TEMPLATE.expectedSha256,Crypto.fileHash(final));assertEquals("legacy remains",legacy.readText())
                observed.put("passed",true);cases.put(observed);progress("RUNNING")
            }
            assertEquals(before,guards());envelope.put("status","PASS").put("owner_registry_and_model_sha256",JSONObject(before)).put("guards_unchanged",true)
                .put("variant",BuildConfig.BUILD_TYPE).put("actual_weight_inference",true).put("raw_reasoning_persisted",false)
                .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET")
                .put("limits","Actual debug unexported importing-subprocess SIGKILL and real main-process startup/native recovery in one live phone/kernel. Main instrumentation/phone are not restarted. Not physical power loss, storage-cache failure, cross-process warm-model lease, system picker, all-slot imports, full F2/M4/product or performance acceptance.")
            File(context.filesDir,"m4-local-asset-import-process-death.json").writeText(envelope.toString(2),Charsets.UTF_8);progress("PASS")
        }catch(failure:Throwable){envelope.put("failure_type",failure.javaClass.simpleName);progress("FAIL");throw failure}
        finally {
            require(root.parentFile!!.canonicalFile==base.canonicalFile && root.name==id)
            Files.walkFileTree(root.toPath(),object:SimpleFileVisitor<Path>() {
                override fun visitFile(file:Path,attrs:BasicFileAttributes):FileVisitResult{Files.delete(file);return FileVisitResult.CONTINUE}
                override fun postVisitDirectory(dir:Path,error:IOException?):FileVisitResult{if(error!=null)throw error;Files.delete(dir);return FileVisitResult.CONTINUE}
            })
        }
    }
}
