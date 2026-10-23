package org.packrag.product

import android.app.Service
import android.content.Intent
import android.net.Uri
import android.os.Binder
import android.os.IBinder
import android.os.Parcel
import android.os.Process
import java.io.File
import java.io.FileOutputStream
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.StandardOpenOption
import java.nio.file.attribute.BasicFileAttributes
import java.time.Instant
import java.util.UUID
import java.util.concurrent.atomic.AtomicBoolean
import org.json.JSONObject

/** Unexported/debug-only; loss of the importing process in a marker-owned UUID test root. */
class AssetImportCrashProbeService:Service() {
    override fun onBind(intent:Intent):IBinder {
        check(BuildConfig.DEBUG && BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        val id=requireNotNull(intent.getStringExtra("test_id"));require(UUID.fromString(id).toString()==id)
        val point=LocalAssetImportStage.valueOf(requireNotNull(intent.getStringExtra("point")))
        require(point in setOf(LocalAssetImportStage.COPYING,LocalAssetImportStage.COMMITTING,LocalAssetImportStage.COMMITTED))
        val parent=File(filesDir,"asset-import-crash");val root=File(parent,id)
        for(file in listOf(filesDir,parent,root)) {
            val attr=Files.readAttributes(file.toPath(),BasicFileAttributes::class.java,LinkOption.NOFOLLOW_LINKS)
            require(attr.isDirectory && !attr.isSymbolicLink)
        }
        require(root.canonicalFile.parentFile==parent.canonicalFile)
        val marker=File(root,"owned-probe-v1");val magic="PackRAG F2 crash root v1\n".toByteArray(Charsets.US_ASCII)
        val markerAttr=Files.readAttributes(marker.toPath(),BasicFileAttributes::class.java,LinkOption.NOFOLLOW_LINKS)
        require(markerAttr.isRegularFile && !markerAttr.isSymbolicLink && markerAttr.size()==magic.size.toLong())
        FileChannel.open(marker.toPath(),StandardOpenOption.READ,LinkOption.NOFOLLOW_LINKS).use{channel->
            val bytes=ByteBuffer.allocate(magic.size+1)
            while(bytes.hasRemaining()){val count=channel.read(bytes);if(count<0)break;check(count>0)}
            require(bytes.position()==magic.size && bytes.array().copyOf(magic.size).contentEquals(magic))
        }
        val status=File(root,"probe-${point.name}.json");check(!Files.exists(status.toPath(),LinkOption.NOFOLLOW_LINKS))
        val started=AtomicBoolean(false)
        val work=Runnable {
            fun record(state:String,event:LocalAssetImportProgress?=null,reason:String?=null) {
                val raw=JSONObject().put("state",state).put("point",point.name).put("pid",Process.myPid()).put("test_id",id)
                    .put("recorded_at",Instant.now().toString()).put("copied_bytes",event?.copiedBytes ?: JSONObject.NULL)
                    .put("expected_bytes",LocalAssetSlot.TEMPLATE.expectedBytes).put("reason",reason ?: JSONObject.NULL).toString().toByteArray(Charsets.UTF_8)
                FileOutputStream(status,false).use{it.write(raw);it.fd.sync()}
            }
            try {
                record("STARTED")
                LocalAssetUriSource(contentResolver,Uri.parse("content://org.packrag.product.test.asset-fixtures/template-valid")).use{source->
                    LocalAssetImporter(File(root,"models"),::syncLocalAssetDirectory).install(LocalAssetSlot.TEMPLATE,source::open,progress={event->
                        if(event.stage==point && (point!=LocalAssetImportStage.COPYING || event.copiedBytes>0)) {
                            record("KILLING",event);Process.killProcess(Process.myPid());error("Probe process kill returned")
                        }
                    })
                }
                record("FAIL",reason="Requested checkpoint never reached")
            }catch(failure:Throwable){record("FAIL",reason=failure.javaClass.simpleName)}
        }
        return object:Binder() {
            override fun onTransact(code:Int,data:Parcel,reply:Parcel?,flags:Int):Boolean {
                if(code==IBinder.FIRST_CALL_TRANSACTION && started.compareAndSet(false,true)) {
                    Thread(work,"packrag-asset-loss-probe").start();reply?.writeNoException();return true
                };return super.onTransact(code,data,reply,flags)
            }
        }
    }
}
