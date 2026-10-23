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
                private val closed=AtomicBoolean(false)
                override fun close() {
                    if(!closed.compareAndSet(false,true)) return
                    try {super.close()} finally {
                        try {descriptor.close()} finally {synchronized(lock){if(input===this) input=null}}
                    }
                }
            }
            synchronized(lock){if(aborted.get()){owned.close();throw LocalAssetImportCancelled()};input=owned}
            return owned
        } catch(failure:Exception){descriptor.close();throw failure}
    }
    fun abort() {
        if(!aborted.compareAndSet(false,true)) return
        // A provider's cancellation IPC/descriptor close must not block the main thread.
        // Independent per-operation workers: a provider IPC cannot starve descriptor close
        // or another operation behind one shared executor. At most one pair per source.
        Thread({runCatching {synchronized(lock){input?.close();input=null}}},"packrag-asset-source-close").apply{isDaemon=true;start()}
        Thread({runCatching {signal.cancel()}},"packrag-asset-source-cancel").apply{isDaemon=true;start()}
    }
    override fun close(){synchronized(lock){val current=input;input=null;current?.close()}}
}

internal fun syncLocalAssetDirectory(path:Path) {
    val descriptor=Os.open(path.toString(),OsConstants.O_RDONLY or OsConstants.O_NOFOLLOW or OsConstants.O_CLOEXEC,0)
    try { check(OsConstants.S_ISDIR(Os.fstat(descriptor).st_mode));Os.fsync(descriptor) } finally { Os.close(descriptor) }
}
