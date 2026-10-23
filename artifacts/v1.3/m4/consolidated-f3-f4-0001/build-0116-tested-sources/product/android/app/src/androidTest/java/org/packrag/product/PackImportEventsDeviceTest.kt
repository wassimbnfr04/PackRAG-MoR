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
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.packs.*

/** Real signed fixtures, Android SQLite and ViewModel transport; generation remains a separate gate. */
@RunWith(AndroidJUnit4::class)
class PackImportEventsDeviceTest {
    private val instrument get()=InstrumentationRegistry.getInstrumentation()
    private val context get()=instrument.targetContext
    private val fixtureName get()=if(BuildConfig.ALLOW_DEVELOPMENT_PACKS) "walking-skeleton.kpack" else "release-trust-corpus/calibration-schema-only.kpack"
    private fun expected()=instrument.context.assets.open("pack-overview-corpus/expectations.json").bufferedReader().use {
        JSONObject(it.readText()).getJSONObject("fixtures").getJSONObject(fixtureName)
    }
    private fun root()=File(context.filesDir,"f3-import-${UUID.randomUUID()}").also { assertTrue(it.mkdir()) }
    private fun fixture(root:File)=File(root,"input.kpack").also { file ->
        instrument.context.assets.open(fixtureName).use { source->file.outputStream().use { source.copyTo(it) } }
        assertEquals(expected().getString("transport_sha256"),Crypto.fileHash(file))
    }
    private fun verifier():PackVerifier {
        val profile=context.assets.open("toolchain.lock.json").bufferedReader().use { JSONObject(it.readText()).getJSONObject("embedder").getJSONObject("pack_profile") }
        val schema=context.assets.open("schema.sql").bufferedReader().use { it.readText() }
        return PackVerifier(ProductConfiguration.keys(context),profile,schema,BuildConfig.ALLOW_DEVELOPMENT_PACKS)
    }
    private fun serialized(events:List<PackImportEvent>)=JSONArray(events.map { event->JSONObject()
        .put("stage",event.stage.name).put("state",event.state.name).put("bytes",event.bytes ?: JSONObject.NULL)
        .put("total_bytes",event.totalBytes ?: JSONObject.NULL) })
    private fun record(name:String,ids:List<String>,before:Map<String,String>,extra:JSONObject) {
        assertEquals(before,LocalAssetImportTestSupport.ownerGuard())
        val cases=JSONArray(ids.map { JSONObject().put("id",it).put("passed",true) })
        File(context.filesDir,name).writeText(extra.put("status","PASS").put("cases",cases)
            .put("owner_registry_and_model_sha256",JSONObject(before)).put("owner_guard_scope","EXPLICIT_50_PUBLIC_BASELINE_FILES_NO_ENUMERATION")
            .put("fixture_sha256",expected().getString("transport_sha256")).put("variant",BuildConfig.BUILD_TYPE)
            .put("actual_weight_inference",false).put("raw_reasoning_persisted",false)
            .put("scope","Actual signed synthetic format/policy/SQLite/import checks. No native generation, system picker, power-loss, genuine calibration/domain or full milestone/release acceptance.").toString(2),Charsets.UTF_8)
    }
    @Test fun realSignedStagesHaveActualByteCountsAndObserverCannotControlActivation() {
        val before=LocalAssetImportTestSupport.ownerGuard();val root=root();val input=fixture(root);val events=mutableListOf<PackImportEvent>()
        try {
            PackRegistry(File(root,"registry"),verifier()).use { registry ->
                val pack=registry.activate(input,observer={events.add(it)})
                assertEquals(expected().getString("pack_id"),pack.id);assertEquals(expected().getString("version"),pack.version)
                assertEquals(expected().getString("manifest_sha256"),Crypto.fileHash(File(pack.root,"manifest.json")))
                assertEquals(listOf("SNAPSHOT_COPY","ARCHIVE_AUDIT","SIGNATURE_AUTHENTICATION","MANIFEST_PROFILE_POLICY","PAYLOAD_INTEGRITY","DATABASE_INDEX","REGISTRY_COMMIT"),
                    events.filter { it.state==PackImportState.STARTED }.map { it.stage.name })
                for(stage in PackImportStage.entries.filter { it!=PackImportStage.SELECTED_DOCUMENT_COPY })
                    assertEquals(1,events.count { it.stage==stage && it.state==PackImportState.PASSED })
                val copy=events.single { it.stage==PackImportStage.SNAPSHOT_COPY && it.state==PackImportState.PASSED }
                val payload=events.single { it.stage==PackImportStage.PAYLOAD_INTEGRITY && it.state==PackImportState.PASSED }
                assertEquals(expected().getLong("transport_bytes"),copy.bytes);assertNull(copy.totalBytes)
                assertEquals(expected().getLong("payload_bytes"),payload.bytes);assertEquals(payload.bytes,payload.totalBytes)
                assertTrue(events.indexOfFirst { it.state==PackImportState.COMMITTED }<events.indexOfLast { it.state==PackImportState.PASSED })
            }
            PackRegistry(File(root,"throwing-observer"),verifier()).use { registry ->
                registry.activate(input,observer={throw AssertionError("Observer cannot authorize or reject")})
                assertEquals(1,registry.snapshot().size)
            }
            record("m4-f3-import-stages.json",listOf("actual-staged-validation-order-and-independent-copy-payload-byte-counts",
                "authenticated-fixture-full-identity","throwing-observer-does-not-change-valid-registry-activation","fifty-owner-public-files-preserved"),before,
                JSONObject().put("events",serialized(events)))
        } finally { LocalAssetImportTestSupport.deleteOwned(root,"f3-import-") }
    }
    @Test fun genuineCommitFaultsReportUncertaintyAndRecoveryMatchesActualDatabaseState() {
        val before=LocalAssetImportTestSupport.ownerGuard();val root=root();val input=fixture(root);val outcomes=JSONArray()
        try {
            for(point in listOf("before_commit","after_commit")) {
                val events=mutableListOf<PackImportEvent>();val directory=File(root,point)
                val failure=PackRegistry(directory,verifier(),fault={if(it==point) throw IllegalStateException("PRIVATE /data/fixture/<attacker>")}).use { registry ->
                    assertThrows(PackImportRejected::class.java) { registry.activate(input,observer={events.add(it)}) }
                }
                assertEquals(PackImportFailure.REGISTRY_RECOVERY_REQUIRED,failure.category)
                assertEquals(PackImportState.RECOVERY_REQUIRED,events.last().state)
                assertFalse(events.any { it.stage==PackImportStage.REGISTRY_COMMIT && it.state==PackImportState.PASSED })
                assertEquals(point=="after_commit",events.any { it.state==PackImportState.COMMITTED })
                val label=safeOperationFailure(failure);assertFalse(label.contains("PRIVATE") || label.contains("/data/") || label.contains("attacker"))
                PackRegistry(directory,verifier()).use { recovered ->
                    assertEquals(if(point=="after_commit") 1 else 0,recovered.snapshot().size)
                    if(point=="after_commit") assertEquals(expected().getString("manifest_sha256"),recovered.snapshot().single().manifestHash)
                }
                outcomes.put(JSONObject().put("fault_point",point).put("safe_category",failure.category.name).put("events",serialized(events)))
            }
            record("m4-f3-import-recovery.json",listOf("before-commit-fault-has-no-database-committed-or-final-pass",
                "after-commit-fault-has-database-committed-but-no-final-pass","uncertain-outcome-reopened-authenticated-registry-matches-commit-state",
                "fifty-owner-public-files-preserved"),before,JSONObject().put("outcomes",outcomes))
        } finally { LocalAssetImportTestSupport.deleteOwned(root,"f3-import-") }
    }
    @Test fun realViewModelImportCapturesAllStagesAndFailedArchiveHasOnlySafeText() {
        val before=LocalAssetImportTestSupport.ownerGuard();val root=root();val input=fixture(root);val registry=File(root,"registry")
        val store=ViewModelStore();lateinit var model:PackRagViewModel
        fun ready(){val end=System.nanoTime()+60_000_000_000L;while(model.state.value.busy && System.nanoTime()<end)android.os.SystemClock.sleep(20);assertFalse(model.state.value.busy)}
        try {
            instrument.runOnMainSync { model=PackRagViewModel(context.applicationContext as Application,registry);store.put("test",model) };ready()
            instrument.runOnMainSync { model.importPack(Uri.fromFile(input)) };ready()
            val accepted=model.state.value
            assertEquals(PackImportStage.entries.toList(),accepted.packImportEvents.map { it.stage })
            assertTrue(accepted.packImportEvents.all { it.state==PackImportState.PASSED });assertEquals(1,accepted.packs.size)
            assertNull(accepted.answer);assertNull(accepted.trace);assertNull(accepted.submission)
            input.writeBytes(byteArrayOf(1,2,3));instrument.runOnMainSync { model.importPack(Uri.fromFile(input)) };ready()
            val rejected=model.state.value;assertEquals("RUNTIME_ERROR",rejected.answer?.state)
            assertTrue(rejected.message.startsWith("ARCHIVE_REJECTED:"));assertFalse(rejected.message.contains("/data/") || rejected.message.contains("<"))
            assertEquals(listOf(PackImportStage.SELECTED_DOCUMENT_COPY,PackImportStage.SNAPSHOT_COPY,PackImportStage.ARCHIVE_AUDIT),rejected.packImportEvents.map { it.stage })
            assertEquals(PackImportState.REJECTED,rejected.packImportEvents.last().state)
            assertEquals(accepted.packs,rejected.packs);assertEquals(expected().getString("manifest_sha256"),rejected.installed.single { it.active }.hash)
            assertTrue(File(registry,".staging").listFiles()!!.isEmpty())
            record("m4-f3-import-viewmodel.json",listOf("real-viewmodel-complete-observed-import-chain",
                "no-query-submission-answer-or-trace-after-import","actual-malformed-selected-file-safe-archive-rejection",
                "prior-active-and-failed-staging-cleanup-preserved","fifty-owner-public-files-preserved"),before,
                JSONObject().put("accepted_events",serialized(accepted.packImportEvents)).put("rejected_events",serialized(rejected.packImportEvents)).put("safe_message",rejected.message))
        } finally {
            instrument.runOnMainSync { store.clear() }
            val end=System.nanoTime()+10_000_000_000L;var released=false
            while(!released && System.nanoTime()<end) {
                released=runCatching { ProductSession(context,registry,ProductConfiguration.keys(context),BuildConfig.ALLOW_DEVELOPMENT_PACKS).use { };true }.getOrDefault(false)
                if(!released)android.os.SystemClock.sleep(50)
            }
            check(released);LocalAssetImportTestSupport.deleteOwned(root,"f3-import-")
        }
    }
}
