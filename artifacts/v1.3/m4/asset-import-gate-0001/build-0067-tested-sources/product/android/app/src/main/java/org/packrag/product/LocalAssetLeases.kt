package org.packrag.product

import java.io.Closeable
import java.nio.file.Path
import java.util.concurrent.atomic.AtomicBoolean

class LocalAssetsBusy:IllegalStateException("LOCAL_ASSETS_BUSY: another session is using these files. Close the other PackRAG window and retry.")

/** Process-local read leases cover actual model mappings; writers never replace a live mapping. */
internal object LocalAssetLeases {
    private class Entry { val readers=mutableSetOf<Any>();var writer:Any?=null }
    private val roots=mutableMapOf<String,Entry>()
    private fun key(root:Path)=root.toAbsolutePath().normalize().toString()
    @Synchronized fun read(root:Path):Closeable=acquire(root,false)
    @Synchronized fun write(root:Path):Closeable=acquire(root,true)
    private fun acquire(root:Path,write:Boolean):Closeable {
        val name=key(root);val entry=roots.getOrPut(name){Entry()}
        if(entry.writer!=null || (write && entry.readers.isNotEmpty())) throw LocalAssetsBusy()
        val token=Any();if(write) entry.writer=token else entry.readers.add(token)
        val closed=AtomicBoolean(false)
        return Closeable {
            if(closed.compareAndSet(false,true)) synchronized(this) {
                val current=checkNotNull(roots[name]);if(write) {check(current.writer===token);current.writer=null} else check(current.readers.remove(token))
                if(current.writer==null && current.readers.isEmpty()) roots.remove(name)
            }
        }
    }
}
