package org.packrag.product

import android.app.Service
import android.content.Intent
import android.os.Binder
import android.os.IBinder
import android.os.Process
import android.os.Parcel
import java.io.File
import java.io.FileOutputStream
import java.util.concurrent.atomic.AtomicBoolean
import org.json.JSONObject
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier

/** Debug-only, unexported, separate-process loss probe; absent from release. */
class RegistryCrashProbeService : Service() {
    override fun onBind(intent: Intent): IBinder {
        val registryPath=intent.getStringExtra("registry")!!; val archivePath=intent.getStringExtra("archive")!!
        val statusPath=intent.getStringExtra("status")!!; val point=intent.getStringExtra("point")!!; val key=intent.getByteArrayExtra("public_key")!!
        require(key.size==32 && point in setOf("after_verify","after_fsync","after_rename","after_version_insert","after_active_write","before_commit","after_commit"))
        fun owned(path: String)=File(path).also { require(it.canonicalPath.startsWith(filesDir.canonicalPath+File.separator)) }
        val registry=owned(registryPath); val archive=owned(archivePath); val status=owned(statusPath)
        val started=AtomicBoolean(false)
        val work=Runnable {
            fun record(state: String,reason: String?=null) {
                val raw=JSONObject().put("state",state).put("point",point).put("pid",Process.myPid()).put("reason",reason ?: JSONObject.NULL).toString().toByteArray(Charsets.UTF_8)
                FileOutputStream(status).use { it.write(raw); it.fd.sync() }
            }
            try {
                val lock=assets.open("toolchain.lock.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
                val schema=assets.open("schema.sql").bufferedReader(Charsets.UTF_8).use { it.readText() }
                val verifier=PackVerifier(listOf(key),lock.getJSONObject("embedder").getJSONObject("pack_profile"),schema,true)
                record("STARTED")
                lateinit var opened: PackRegistry
                opened=PackRegistry(registry,verifier,testCachePages=1) { current ->
                    if(current==point) {
                        if(current in setOf("after_version_insert","after_active_write","before_commit")) opened.forceProbePageSpill()
                        record("KILLING"); Process.killProcess(Process.myPid()); error("Process kill returned unexpectedly")
                    }
                }
                opened.use { it.activate(archive) }
                record("FAIL","Requested checkpoint was never reached")
            } catch(error: Throwable) { record("FAIL",error.message?.take(256) ?: error.javaClass.name) }
        }
        return object : Binder() {
            override fun onTransact(code: Int,data: Parcel,reply: Parcel?,flags: Int): Boolean {
                if(code==IBinder.FIRST_CALL_TRANSACTION && started.compareAndSet(false,true)) {
                    Thread(work,"packrag-registry-loss-probe").start(); reply?.writeNoException(); return true
                }
                return super.onTransact(code,data,reply,flags)
            }
        }
    }
}
