package org.packrag.product

import android.content.ContentResolver
import android.net.Uri
import android.os.CancellationSignal
import android.system.Os
import android.system.OsConstants
import java.io.Closeable
import java.io.FilterInputStream
import java.io.InputStream
import java.nio.file.Path
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

/** One platform descriptor open; never queries filenames/sizes or persists the external URI. */
internal class LocalAssetUriSource(private val resolver:ContentResolver,private val uri:Uri):Closeable {
    private val signal=CancellationSignal()
    private val opened=AtomicBoolean(false)
    private val aborted=AtomicBoolean(false)
    private val lock=Any()
    private var input:InputStream?=null
    init { require(uri.scheme=="content") { "LOCAL_ASSET_CONTENT_URI_REQUIRED" } }
    fun open():InputStream {
        check(opened.compareAndSet(false,true)) { "LOCAL_ASSET_SOURCE_ALREADY_OPENED" }
        if(aborted.get()) throw LocalAssetImportCancelled()
        val descriptor=requireNotNull(resolver.openAssetFileDescriptor(uri,"r",signal)) { "LOCAL_ASSET_SOURCE_UNAVAILABLE" }
        try {
            val stream=descriptor.createInputStream()
            val owned=object:FilterInputStream(stream) {
                override fun close() {
                    try { super.close() } finally { descriptor.close();synchronized(lock){if(input===this) input=null} }
                }
            }
            synchronized(lock){if(aborted.get()){owned.close();throw LocalAssetImportCancelled()};input=owned}
            return owned
        } catch(failure:Exception){descriptor.close();throw failure}
    }
    fun abort() {
        aborted.set(true)
        // A provider's cancellation IPC/descriptor close must not block the main thread.
        aborts.execute {
            runCatching { synchronized(lock){input?.close();input=null} }
            runCatching { signal.cancel() }
        }
    }
    override fun close(){synchronized(lock){input?.close();input=null}}
    companion object {
        private val aborts=Executors.newSingleThreadExecutor { action -> Thread(action,"packrag-asset-source-close").apply {isDaemon=true} }
    }
}

internal fun syncLocalAssetDirectory(path:Path) {
    val descriptor=Os.open(path.toString(),OsConstants.O_RDONLY or OsConstants.O_NOFOLLOW or OsConstants.O_CLOEXEC,0)
    try { check(OsConstants.S_ISDIR(Os.fstat(descriptor).st_mode));Os.fsync(descriptor) } finally { Os.close(descriptor) }
}
