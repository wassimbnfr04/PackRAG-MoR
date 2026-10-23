package org.packrag.product

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.os.IBinder
import android.os.Process
import android.os.Parcel
import android.os.DeadObjectException
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.io.RandomAccessFile
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
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier

@RunWith(AndroidJUnit4::class)
class RegistryProcessDeathDeviceTest {
    @Test fun abruptSeparateProcessDeathAndHotJournalRecovery() {
        val instrument=InstrumentationRegistry.getInstrumentation(); val context=instrument.targetContext; val assets=instrument.context.assets
        val corpus=assets.open("lifecycle-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val key=assets.open("lifecycle-corpus/public-key.raw").use { it.readBytes() }; assertEquals(corpus.getString("public_key_sha256"),Crypto.sha256(key))
        val profile=assets.open("parity-reference.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()).getJSONObject("lock").getJSONObject("embedder").getJSONObject("pack_profile") }
        val schema=assets.open("schema.sql").bufferedReader(Charsets.UTF_8).use { it.readText() }; val verifier=PackVerifier(listOf(key),profile,schema,true)
        val root=File(context.filesDir,"m3-death-${UUID.randomUUID()}"); assertTrue(root.mkdirs()); val inputs=mutableMapOf<String,File>(); val hashes=mutableMapOf<String,String>(); val results=JSONArray()
        val component=ComponentName(context.packageName,"org.packrag.product.RegistryCrashProbeService")
        val service=context.packageManager.getServiceInfo(component,0); assertFalse(service.exported); assertEquals(context.packageName+":registry_crash_probe",service.processName)
        try {
            val cases=corpus.getJSONArray("cases")
            for(i in 0 until cases.length()) {
                val case=cases.getJSONObject(i); val file=File(root,case.getString("filename"))
                assets.open("lifecycle-corpus/"+file.name).use { source -> file.outputStream().use { source.copyTo(it) } }
                assertEquals(case.getString("sha256"),Crypto.fileHash(file)); inputs[case.getString("id")]=file; hashes[case.getString("id")]=case.getString("manifest_sha256")
            }
            val id="org.packrag.development.walking-skeleton"
            for(point in listOf("after_verify","after_fsync","after_rename","after_version_insert","after_active_write","before_commit","after_commit")) {
                val registryRoot=File(root,"registry-$point"); val status=File(root,"status-$point.json"); var oldDbHash=""; var oldDenseHash=""
                PackRegistry(registryRoot,verifier).use { val pack=it.activate(inputs.getValue("v1")); oldDbHash=Crypto.fileHash(File(pack.root,"knowledge.sqlite")); oldDenseHash=Crypto.fileHash(File(pack.root,"dense.kdx")) }
                val connected=CountDownLatch(1); val killed=CountDownLatch(1); val bound=AtomicBoolean(false); var remote: IBinder?=null
                val connection=object : ServiceConnection {
                    override fun onServiceConnected(name: ComponentName,binder: IBinder) { remote=binder; connected.countDown() }
                    override fun onServiceDisconnected(name: ComponentName) { if(bound.compareAndSet(true,false)) context.unbindService(this); killed.countDown() }
                    override fun onBindingDied(name: ComponentName) { if(bound.compareAndSet(true,false)) context.unbindService(this); killed.countDown() }
                    override fun onNullBinding(name: ComponentName) { connected.countDown() }
                }
                val intent=Intent().setComponent(component).putExtra("registry",registryRoot.absolutePath).putExtra("archive",inputs.getValue("v2").absolutePath)
                    .putExtra("status",status.absolutePath).putExtra("point",point).putExtra("public_key",key)
                bound.set(true)
                try {
                    assertTrue("Could not bind debug loss probe",context.bindService(intent,connection,Context.BIND_AUTO_CREATE))
                    assertTrue("Probe did not connect",connected.await(60,TimeUnit.SECONDS))
                    val request=Parcel.obtain(); val response=Parcel.obtain()
                    try { try { assertTrue(remote!!.transact(IBinder.FIRST_CALL_TRANSACTION,request,response,0)); response.readException() } catch(dead: DeadObjectException) { /* Kill can race the successful trigger reply; status and disconnect are mandatory below. */ } }
                    finally { request.recycle(); response.recycle() }
                    assertTrue("Probe did not die at $point",killed.await(60,TimeUnit.SECONDS))
                } finally { if(bound.compareAndSet(true,false)) context.unbindService(connection) }
                val probe=JSONObject(status.readText(Charsets.UTF_8)); assertEquals(probe.toString(),"KILLING",probe.getString("state")); assertEquals(point,probe.getString("point")); assertNotEquals(Process.myPid(),probe.getInt("pid"))
                // Record the hot-journal presence BEFORE reopening. DELETE-mode
                // journal is expected while inside the interrupted transaction.
                val journal=File(registryRoot,"registry.sqlite-journal"); val journalBefore=journal.exists(); val journalBytes=if(journalBefore) journal.length() else 0L
                val journalHeader=if(journalBytes>=28) RandomAccessFile(journal,"r").use { file -> ByteArray(28).also { file.readFully(it) } } else byteArrayOf()
                val journalMagic=journalHeader.take(8).joinToString("") { "%02x".format(it.toInt() and 255) }
                if(point in listOf("after_version_insert","after_active_write","before_commit")) { assertTrue(journalBytes>512); assertEquals("No hot SQLite journal at $point", "d9d505f920a163d7",journalMagic) }
                PackRegistry(registryRoot,verifier).use { recovered ->
                    val committed=point=="after_commit"; val expected=if(committed) "v2" else "v1"; val pack=recovered.snapshot().single()
                    assertEquals(hashes.getValue(expected),pack.manifestHash); assertFalse(pack.sparse("\"Aster\"").isEmpty())
                    assertEquals(oldDbHash,Crypto.fileHash(File(registryRoot,"packs/$id/1.0.0/knowledge.sqlite"))); assertEquals(oldDenseHash,Crypto.fileHash(File(registryRoot,"packs/$id/1.0.0/dense.kdx")))
                    assertEquals(if(committed) 2 else 1,recovered.installed().size); assertEquals(committed,File(registryRoot,"packs/$id/1.0.1").exists()); assertEquals(0,File(registryRoot,".staging").listFiles()!!.size)
                    assertTrue(recovered.verificationFailures().isEmpty())
                    results.put(JSONObject().put("id","actual-process-death-$point").put("passed",true).put("probe",probe).put("journal_existed_before_reopen",journalBefore)
                        .put("journal_bytes_before_reopen",journalBytes).put("journal_header_hex",journalHeader.joinToString("") { "%02x".format(it.toInt() and 255) })
                        .put("probe_cache_pages",1).put("test_transaction_pressure_bytes",if(point in listOf("after_version_insert","after_active_write","before_commit")) 1048576 else 0)
                        .put("actual_active_version",pack.version).put("manifest_sha256",pack.manifestHash).put("old_payloads_unchanged",true))
                }
                File(context.filesDir,"m3-process-death-progress.json").writeText(JSONObject().put("status","RUNNING").put("cases",results).toString(2),Charsets.UTF_8)
            }
            for(i in 0 until cases.length()) { val case=cases.getJSONObject(i); assertEquals(case.getString("sha256"),Crypto.fileHash(inputs.getValue(case.getString("id")))) }
            File(context.filesDir,"m3-process-death.json").writeText(JSONObject().put("status","PASS").put("cases",results).put("corpus",corpus)
                .put("purpose","ACTUAL_ANDROID_SEPARATE_PROCESS_SIGKILL_AT_FSYNC_RENAME_SQLITE_CHECKPOINTS")
                .put("limits","Actual app subprocess death and journal recovery; not physical power loss or hardware storage-cache failure. Probe is debug-only and unexported.").toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator)); root.deleteRecursively() }
    }
}
