package org.packrag.product

import android.app.Application
import android.content.Context
import android.content.ContextWrapper
import androidx.lifecycle.ViewModelStore
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

/** Real app/session/native controls in owned roots; never change an owner model file. */
@RunWith(AndroidJUnit4::class)
class LocalAssetReadinessDeviceTest {
    private val instrument get()=InstrumentationRegistry.getInstrumentation()
    private val context get()=instrument.targetContext
    private val question="What is the maximum continuous operating temperature of the Aster-9?"
    private val query get()=Query(question,"2027-01-01",null,true)
    private class PrivateContext(base:Context,private val root:File):ContextWrapper(base) {
        override fun getFilesDir()=root
    }
    private class PrivateApplication(base:Context,private val root:File):Application() {
        init { attachBaseContext(base) }
        override fun getFilesDir()=root
    }
    private fun guards():Map<String,String> {
        val result=sortedMapOf<String,String>()
        for(name in listOf("packs","production-registry","models")) {
            val folder=File(context.filesDir,name).toPath()
            if(!Files.exists(folder,LinkOption.NOFOLLOW_LINKS)) continue
            Files.walkFileTree(folder,object:SimpleFileVisitor<Path>() {
                override fun preVisitDirectory(dir:Path,attrs:BasicFileAttributes):FileVisitResult {
                    return if(dir.fileName.toString() in setOf(".private","temp","stage","pytest-temp")) FileVisitResult.SKIP_SUBTREE else FileVisitResult.CONTINUE
                }
                override fun visitFile(file:Path,attrs:BasicFileAttributes):FileVisitResult {
                    check(!attrs.isSymbolicLink);if(attrs.isRegularFile) result[file.toFile().relativeTo(context.filesDir).invariantSeparatorsPath]=Crypto.fileHash(file.toFile())
                    return FileVisitResult.CONTINUE
                }
            })
        }
        return result
    }
    private fun fixture(root:File):File {
        val input=File(root,"input.kpack")
        val name=if(BuildConfig.ALLOW_DEVELOPMENT_PACKS) "walking-skeleton.kpack" else "release-trust-corpus/calibration-schema-only.kpack"
        instrument.context.assets.open(name).use { source -> input.outputStream().use { source.copyTo(it) } }
        assertEquals(if(BuildConfig.ALLOW_DEVELOPMENT_PACKS) "19da286b9f0860c312dc8d14ce0ee8681bf12ca092a7b8a12171fd86abe02c7f" else
            "eb1d477f32e60ce97784320994d473690dd97ff4d13b49d921c93aad82b58011",Crypto.fileHash(input))
        return input
    }
    private fun ownModelReferences(root:File) {
        // Only immutable reads of these three owner files. Template is a separate copy
        // so corruption/recovery controls can never write through an owner hardlink.
        for(slot in LocalAssetSlot.entries) {
            val source=File(context.filesDir,"models/${slot.relativePath}")
            val target=File(root,"models/${slot.relativePath}");check(target.parentFile!!.mkdirs() || target.parentFile!!.isDirectory)
            assertFalse(Files.exists(target.toPath(),LinkOption.NOFOLLOW_LINKS))
            if(slot==LocalAssetSlot.TEMPLATE) source.copyTo(target) else Files.createLink(target.toPath(),source.toPath())
        }
    }
    private fun record(name:String,cases:JSONArray,before:Map<String,String>,extra:JSONObject=JSONObject()) {
        assertEquals(before,guards())
        File(context.filesDir,name).writeText(extra.put("status","PASS").put("cases",cases)
            .put("owner_registry_and_model_sha256",JSONObject(before)).put("guards_unchanged",true)
            .put("variant",BuildConfig.BUILD_TYPE).put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET")
            .put("limits","Synthetic functional acceptance, not final domain expertise, licensing/review/calibration approval, gold accuracy or performance benchmark.").toString(2),Charsets.UTF_8)
    }
    private fun removeOwn(root:File) {
        require(root.parentFile!!.canonicalFile==context.filesDir.canonicalFile)
        // walkFileTree does not follow links; delete only this newly owned root.
        Files.walkFileTree(root.toPath(),object:SimpleFileVisitor<Path>() {
            override fun visitFile(file:Path,attrs:BasicFileAttributes):FileVisitResult { Files.delete(file);return FileVisitResult.CONTINUE }
            override fun postVisitDirectory(dir:Path,error:java.io.IOException?):FileVisitResult { if(error!=null) throw error;Files.delete(dir);return FileVisitResult.CONTINUE }
        })
    }
    @Test fun missingCorruptAndSymlinkPathsRejectBeforeAnyNativeInitialization() {
        val before=guards();val root=File(context.filesDir,"asset-negative-${UUID.randomUUID()}");assertTrue(root.mkdir())
        val cases=JSONArray();fun passed(id:String){cases.put(JSONObject().put("id",id).put("passed",true))}
        try {
            ProductSession(PrivateContext(context,root),File(root,"registry"),ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS).use { session ->
                val empty=session.ask(query);assertEquals("NO_ACTIVE_PACK",empty.answer.state)
                assertNull(empty.session!!.generator);assertFalse(empty.session!!.embedderInitialized)
                assertTrue(session.localAssetStatuses().all { it.condition==LocalAssetCondition.UNCHECKED })
                passed("no-pack-missing-assets-skips-verification-and-models")
                session.registry.activate(fixture(root))
                val missing=assertThrows(LocalAssetsUnavailable::class.java) { session.ask(query) }
                assertTrue(missing.statuses.all { it.condition==LocalAssetCondition.MISSING });assertTrue(missing.message!!.startsWith("LOCAL_ASSET_MISSING"))
                assertNull(session.generatorLoadAndVerificationMs);passed("active-pack-missing-assets-blocks-constructors")
                val models=File(root,"models");assertTrue(models.mkdir())
                val template=File(models,LocalAssetSlot.TEMPLATE.relativePath);template.writeBytes(ByteArray(5443))
                val corrupt=assertThrows(LocalAssetsUnavailable::class.java) { session.ask(query) }
                assertEquals(LocalAssetCondition.CORRUPT,corrupt.statuses.single { it.spec.slot==LocalAssetSlot.TEMPLATE }.condition)
                assertNull(session.generatorLoadAndVerificationMs);passed("correct-size-corrupt-template-blocks-constructors")
                val target=File(root,"unrelated-original");target.writeText("do not change")
                val original=Crypto.fileHash(target);val generator=File(models,LocalAssetSlot.GENERATOR.relativePath)
                Files.createSymbolicLink(generator.toPath(),target.toPath())
                val leaf=session.verifyLocalAssets();assertEquals(LocalAssetCondition.UNSAFE_PATH,leaf.first().condition)
                Files.delete(generator.toPath());assertTrue(File(models,"granite").mkdir())
                Files.delete(File(models,"granite").toPath());Files.createSymbolicLink(File(models,"granite").toPath(),root.toPath())
                val parent=session.verifyLocalAssets();assertTrue(parent.filter { it.spec.slot in listOf(LocalAssetSlot.TOKENIZER,LocalAssetSlot.ENCODER) }.all { it.condition==LocalAssetCondition.UNSAFE_PATH })
                assertEquals(original,Crypto.fileHash(target));passed("actual-leaf-and-parent-symlinks-never-followed")
                Files.delete(File(models,"granite").toPath());Files.createSymbolicLink(File(root,"linked-root").toPath(),models.toPath())
                assertTrue(LocalAssetVerifier(File(root,"linked-root")).verify().all { it.condition==LocalAssetCondition.UNSAFE_PATH })
                assertNull(session.generatorLoadAndVerificationMs);passed("actual-model-root-symlink-rejected")
            }
            record("m4-local-assets-negative.json",cases,before)
        } finally { removeOwn(root) }
    }
    @Test fun actualPinnedColdWarmEvidenceAndOwnedTemplateCorruptionReleaseAndRecoverModels() {
        val before=guards();val root=File(context.filesDir,"asset-runtime-${UUID.randomUUID()}");assertTrue(root.mkdir())
        val cases=JSONArray();fun passed(id:String){cases.put(JSONObject().put("id",id).put("passed",true))}
        lateinit var cold:RuntimeTrace
        try {
            ownModelReferences(root)
            ProductSession(PrivateContext(context,root),File(root,"registry"),ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS).use { session ->
                val checked=session.verifyLocalAssets();assertTrue(checked.all { it.condition==LocalAssetCondition.VERIFIED })
                assertNull(session.generatorLoadAndVerificationMs);passed("all-four-real-pins-check-without-native-initialization")
                session.registry.activate(fixture(root));cold=session.ask(query)
                fun accepted(trace:RuntimeTrace) {
                    assertEquals("ANSWER_ACCEPTED",trace.answer.state);assertTrue(trace.answer.text!!.contains("74 °C"));assertTrue(trace.answer.text!!.contains("[S1]"))
                    assertFalse(trace.answer.text!!.contains("</think>"));assertEquals("266af80f5d4da1dac500acd9a2bcc1fd2317b2caf49141ebb586280b9df49333",trace.answer.sources.single().canonicalTextSha256)
                    assertTrue(trace.diagnostics!!.generationCalled);assertEquals(query,trace.evidenceContext!!.query);assertTrue(trace.session!!.embedderInitialized)
                    assertNotNull(trace.session!!.generator);assertTrue(trace.emittedTokens in 1..512)
                }
                accepted(cold);assertTrue(cold.initializationMs>0);val warm=session.ask(query);accepted(warm);assertEquals(0.0,warm.initializationMs,0.0)
                passed("real-cold-warm-pinned-LFM-evidence-citations-validation")
                val excluded=session.ask(query.copy(jurisdiction="MA"));assertEquals("NO_RELEVANT_EVIDENCE",excluded.answer.state)
                assertEquals(0,excluded.emittedTokens);assertFalse(excluded.diagnostics!!.generationCalled);passed("jurisdiction-excluded-evidence-abstains-without-generation")
                val copied=File(root,"models/${LocalAssetSlot.TEMPLATE.relativePath}");copied.writeBytes(ByteArray(5443))
                val bad=session.verifyLocalAssets();assertEquals(LocalAssetCondition.CORRUPT,bad.single { it.spec.slot==LocalAssetSlot.TEMPLATE }.condition)
                assertNull(session.generatorLoadAndVerificationMs)
                assertThrows(LocalAssetsUnavailable::class.java) { session.ask(query) };assertNull(session.generatorLoadAndVerificationMs)
                assertEquals("ANSWER_ACCEPTED",cold.answer.state);passed("explicit-corruption-check-releases-warm-models-and-next-query-blocks")
                File(context.filesDir,"models/${LocalAssetSlot.TEMPLATE.relativePath}").copyTo(copied,overwrite=true)
                assertTrue(session.verifyLocalAssets().all { it.condition==LocalAssetCondition.VERIFIED });assertNull(session.generatorLoadAndVerificationMs)
                val recovered=session.ask(query);accepted(recovered);assertTrue(recovered.initializationMs>0)
                passed("restored-owned-template-reverifies-and-real-native-query-recovers")
            }
            record("m4-local-assets-runtime.json",cases,before,JSONObject().put("actual_weight_inference",true).put("answer",cold.answer.text)
                .put("prefill_tokens",cold.prefillTokens).put("evidence_tokens",cold.evidenceTokens).put("emitted_tokens",cold.emittedTokens)
                .put("initialization_ms",cold.initializationMs).put("session_wall_ms",cold.totalMs).put("raw_reasoning_persisted",false))
        } finally { removeOwn(root) }
    }
    @Test fun actualViewModelRetainsFailedAssetObservationAndReadOnlyCheckOwnsCompletedAnswer() {
        val before=guards();val root=File(context.filesDir,"asset-model-${UUID.randomUUID()}");assertTrue(root.mkdir())
        val store=ViewModelStore();lateinit var model:PackRagViewModel;val cases=JSONArray()
        fun passed(id:String){cases.put(JSONObject().put("id",id).put("passed",true))}
        fun ready(){val end=System.nanoTime()+600_000_000_000L;while(model.state.value.busy && System.nanoTime()<end) android.os.SystemClock.sleep(20);assertFalse(model.state.value.busy)}
        try {
            ProductSession(PrivateContext(context,root),File(root,"registry"),ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS).use { it.registry.activate(fixture(root)) }
            instrument.runOnMainSync { model=PackRagViewModel(PrivateApplication(context,root),File(root,"registry"));store.put("model",model) };ready()
            instrument.runOnMainSync { model.ask(question,"2027-01-01","",true) };ready()
            val failed=model.state.value;assertEquals("RUNTIME_ERROR",failed.answer?.state);assertTrue(failed.message.startsWith("LOCAL_ASSET_MISSING"))
            assertEquals(4,failed.localAssets.size);assertTrue(failed.localAssets.all { it.condition==LocalAssetCondition.MISSING && it.checkedAt!=null })
            assertEquals(question,failed.submission!!.query.raw);assertNull(failed.trace);assertNull(failed.completedResultId)
            passed("failed-query-asset-observations-survive-session-recovery-with-time-and-actionable-error")
            ownModelReferences(root);instrument.runOnMainSync { model.checkLocalAssets() };ready()
            assertTrue(model.state.value.localAssets.all { it.condition==LocalAssetCondition.VERIFIED });assertSame(failed.answer,model.state.value.answer)
            instrument.runOnMainSync { model.ask(question,"2027-01-01","",true) };ready()
            val completed=model.state.value;assertEquals("ANSWER_ACCEPTED",completed.answer?.state);assertTrue(completed.answer!!.text!!.contains("74 °C"))
            assertNotNull(completed.completedResultId);assertNotNull(completed.trace)
            instrument.runOnMainSync { model.checkLocalAssets() };ready()
            val after=model.state.value;assertSame(completed.answer,after.answer);assertSame(completed.trace,after.trace);assertSame(completed.submission,after.submission)
            assertEquals(completed.completedResultId,after.completedResultId);assertTrue(after.localAssets.all { it.condition==LocalAssetCondition.VERIFIED })
            passed("real-answer-trace-submission-and-completion-identity-survive-actual-read-only-check")
            assertTrue(failed.localAssets.all { it.condition==LocalAssetCondition.MISSING });passed("old-failed-status-values-remain-owned-after-later-success")
            record("m4-local-assets-viewmodel.json",cases,before,JSONObject().put("actual_weight_inference",true).put("raw_reasoning_persisted",false))
        } finally {
            instrument.runOnMainSync { store.clear() }
            val end=System.nanoTime()+10_000_000_000L;var released=false
            while(!released && System.nanoTime()<end) {
                released=runCatching { ProductSession(PrivateContext(context,root),File(root,"registry"),ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS).use { };true }.getOrDefault(false)
                if(!released) android.os.SystemClock.sleep(50)
            }
            check(released);removeOwn(root)
        }
    }
}
