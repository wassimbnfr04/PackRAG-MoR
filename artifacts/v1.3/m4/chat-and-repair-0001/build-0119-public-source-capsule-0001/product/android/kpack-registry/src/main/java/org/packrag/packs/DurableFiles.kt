package org.packrag.packs

import android.system.Os
import android.system.OsConstants
import java.io.File
import java.io.RandomAccessFile
import java.nio.file.Files

/** App-private, same-filesystem durability. Never follows caller-provided trees. */
internal object DurableFiles {
    fun directory(file: File) {
        val descriptor = Os.open(file.absolutePath, OsConstants.O_RDONLY, 0)
        try { require(OsConstants.S_ISDIR(Os.fstat(descriptor).st_mode)); Os.fsync(descriptor) } finally { Os.close(descriptor) }
    }
    fun tree(root: File) {
        Files.walk(root.toPath()).use { paths ->
            val entries = paths.iterator().asSequence().toList()
            require(entries.none { Files.isSymbolicLink(it) })
            for(path in entries.filter { Files.isRegularFile(it) }) RandomAccessFile(path.toFile(),"rw").use { it.fd.sync() }
            entries.filter { Files.isDirectory(it) }.sortedByDescending { it.nameCount }.forEach { directory(it.toFile()) }
        }
    }
    fun rename(source: File, target: File) {
        require(!target.exists() && source.parentFile!!.canonicalPath != target.canonicalPath)
        Os.rename(source.absolutePath,target.absolutePath)
        directory(source.parentFile!!); directory(target.parentFile!!)
    }
}
