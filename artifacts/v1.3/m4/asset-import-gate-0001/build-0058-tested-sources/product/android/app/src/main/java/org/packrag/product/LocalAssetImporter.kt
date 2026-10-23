package org.packrag.product

import java.io.File
import java.io.InputStream
import java.nio.ByteBuffer
import java.nio.channels.Channels
import java.nio.channels.FileChannel
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.NoSuchFileException
import java.nio.file.Path
import java.nio.file.StandardCopyOption
import java.nio.file.StandardOpenOption
import java.nio.file.attribute.BasicFileAttributes
import java.security.MessageDigest
import java.time.Instant
import java.util.UUID

enum class LocalAssetImportStage { COPYING,VERIFYING,SYNCING,COMMITTING,COMMITTED }
data class LocalAssetImportProgress(val slot:LocalAssetSlot,val stage:LocalAssetImportStage,val copiedBytes:Long,val expectedBytes:Long)
data class LocalAssetImportResult(val slot:LocalAssetSlot,val bytes:Long,val sha256:String,val completedAt:String,val directorySynced:Boolean)
class LocalAssetImportFailed(val code:String):IllegalStateException("$code: the existing asset was not installed by this operation.")
class LocalAssetImportCancelled:IllegalStateException("LOCAL_ASSET_IMPORT_CANCELLED: cancelled before installation.")

/** Only fixed slots; private CREATE_NEW staging, observed bytes, read-back pin and atomic move. */
class LocalAssetImporter(root:File,private val syncDirectory:(Path)->Unit,
    private val specs:List<LocalAssetSpec> = LocalAssetSlot.entries.map { LocalAssetSpec(it) }) {
    private val root=root.toPath().toAbsolutePath().normalize()
    private val namespace=this.root.resolve(".asset-import-v1")
    private val marker=namespace.resolve("owner.marker")
    private val magic="PackRAG owned asset import v1\n".toByteArray(Charsets.US_ASCII)
    private val pins=specs.associateBy { it.slot }
    private val stageName=Regex("(GENERATOR|TEMPLATE|TOKENIZER|ENCODER)-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\\.part")
    init { require(pins.size==specs.size && pins.isNotEmpty()) }
    private fun attributes(path:Path):BasicFileAttributes?=try { Files.readAttributes(path,BasicFileAttributes::class.java,LinkOption.NOFOLLOW_LINKS) } catch(missing:NoSuchFileException){null}
    private fun directory(path:Path,create:Boolean=false) {
        var value=attributes(path)
        if(value==null && create) {Files.createDirectory(path);value=attributes(path)}
        if(value==null || value.isSymbolicLink || !value.isDirectory) throw LocalAssetImportFailed("LOCAL_ASSET_UNSAFE_PATH")
    }
    private fun destination(spec:LocalAssetSpec,create:Boolean):Path {
        directory(root.parent);directory(root,create)
        var path=root;val parts=spec.slot.relativePath.split('/')
        for(part in parts.dropLast(1)) {path=path.resolve(part);directory(path,create)}
        path=path.resolve(parts.last());val value=attributes(path)
        if(value!=null && (value.isSymbolicLink || !value.isRegularFile)) throw LocalAssetImportFailed("LOCAL_ASSET_UNSAFE_PATH")
        return path
    }
    private fun namespaceIsOwned() {
        directory(namespace);val value=attributes(marker)
        if(value==null || value.isSymbolicLink || !value.isRegularFile || value.size()!=magic.size.toLong()) throw LocalAssetImportFailed("LOCAL_ASSET_STAGING_UNSAFE")
        if(!Files.readAllBytes(marker).contentEquals(magic)) throw LocalAssetImportFailed("LOCAL_ASSET_STAGING_UNSAFE")
    }
    private fun reconcileOwned():Int {
        if(attributes(namespace)==null) return 0
        namespaceIsOwned();val staged=mutableListOf<Path>();var entries=0
        Files.newDirectoryStream(namespace).use { stream ->
            for(path in stream) {
                if(++entries>129) throw LocalAssetImportFailed("LOCAL_ASSET_STAGING_UNSAFE")
                if(path==marker) continue
                val match=stageName.matchEntire(path.fileName.toString()) ?: throw LocalAssetImportFailed("LOCAL_ASSET_STAGING_UNSAFE")
                val spec=pins[LocalAssetSlot.valueOf(match.groupValues[1])] ?: throw LocalAssetImportFailed("LOCAL_ASSET_STAGING_UNSAFE")
                val value=attributes(path)
                if(value==null || value.isSymbolicLink || !value.isRegularFile || value.size() !in 0..spec.bytes) throw LocalAssetImportFailed("LOCAL_ASSET_STAGING_UNSAFE")
                staged.add(path)
            }
        }
        // Validate the entire flat owned namespace before deleting any entry. Never recurse.
        staged.forEach { Files.delete(it) };Files.delete(marker);Files.delete(namespace);return staged.size
    }
    fun reconcile():Int=LocalAssetLeases.write(root).use {
        if(attributes(root)==null) 0 else {directory(root);reconcileOwned()}
    }
    private fun createNamespace() {
        Files.createDirectory(namespace)
        FileChannel.open(marker,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE,LinkOption.NOFOLLOW_LINKS).use { channel ->
            val buffer=ByteBuffer.wrap(magic);while(buffer.hasRemaining()) if(channel.write(buffer)<=0) throw LocalAssetImportFailed("LOCAL_ASSET_IMPORT_IO")
            channel.force(true)
        }
        syncDirectory(namespace)
    }
    fun install(slot:LocalAssetSlot,openInput:()->InputStream,cancelled:()->Boolean={false},
        progress:(LocalAssetImportProgress)->Unit={}):LocalAssetImportResult=LocalAssetLeases.write(root).use {
        val spec=requireNotNull(pins[slot]);var copied=0L;var stage:Path?=null;var committed=false
        fun cancel(){if(cancelled()) throw LocalAssetImportCancelled()}
        fun emit(phase:LocalAssetImportStage){runCatching {progress(LocalAssetImportProgress(slot,phase,copied,spec.bytes))}}
        try {
            cancel();directory(root.parent);directory(root,true)
            // Existing final paths are checked without creating new nested destinations yet.
            var parent=root
            for(part in slot.relativePath.split('/').dropLast(1)) {
                parent=parent.resolve(part);val value=attributes(parent)
                if(value==null) break
                if(value.isSymbolicLink || !value.isDirectory) throw LocalAssetImportFailed("LOCAL_ASSET_UNSAFE_PATH")
            }
            val old=attributes(root.resolve(slot.relativePath))
            if(old!=null && (old.isSymbolicLink || !old.isRegularFile)) throw LocalAssetImportFailed("LOCAL_ASSET_UNSAFE_PATH")
            reconcileOwned();createNamespace()
            stage=namespace.resolve("${slot.name}-${UUID.randomUUID()}.part")
            emit(LocalAssetImportStage.COPYING)
            FileChannel.open(stage,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE,LinkOption.NOFOLLOW_LINKS).use { channel ->
                openInput().use { source ->
                    val buffer=ByteArray(65536)
                    while(true) {
                        cancel();var count=source.read(buffer)
                        if(count<0) break
                        if(count==0) {val one=source.read();if(one<0) break;buffer[0]=one.toByte();count=1}
                        if(count !in 1..buffer.size || copied+count>spec.bytes) throw LocalAssetImportFailed("LOCAL_ASSET_IMPORT_WRONG_SIZE")
                        val bytes=ByteBuffer.wrap(buffer,0,count)
                        while(bytes.hasRemaining()) {cancel();if(channel.write(bytes)<=0) throw LocalAssetImportFailed("LOCAL_ASSET_IMPORT_IO")}
                        copied+=count;emit(LocalAssetImportStage.COPYING)
                    }
                }
                cancel();if(copied!=spec.bytes) throw LocalAssetImportFailed("LOCAL_ASSET_IMPORT_WRONG_SIZE")
                emit(LocalAssetImportStage.SYNCING);channel.force(true)
            }
            cancel();emit(LocalAssetImportStage.VERIFYING)
            val digest=MessageDigest.getInstance("SHA-256");var observed=0L
            Channels.newInputStream(FileChannel.open(stage,StandardOpenOption.READ,LinkOption.NOFOLLOW_LINKS)).use { input ->
                val buffer=ByteArray(65536)
                while(true) {cancel();val count=input.read(buffer);if(count<0) break
                    if(count==0 || observed+count>spec.bytes) throw LocalAssetImportFailed("LOCAL_ASSET_IMPORT_IO")
                    observed+=count;digest.update(buffer,0,count)
                }
            }
            val actual=digest.digest().joinToString(""){(it.toInt() and 255).toString(16).padStart(2,'0')}
            if(observed!=spec.bytes || actual!=spec.sha256) throw LocalAssetImportFailed("LOCAL_ASSET_IMPORT_HASH_MISMATCH")
            syncDirectory(namespace);val final=destination(spec,true)
            cancel();emit(LocalAssetImportStage.COMMITTING);cancel()
            Files.move(stage,final,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING)
            committed=true;stage=null
            val synced=runCatching {syncDirectory(final.parent)}.isSuccess
            emit(LocalAssetImportStage.COMMITTED)
            LocalAssetImportResult(slot,observed,actual,Instant.now().toString(),synced)
        } catch(cancel:LocalAssetImportCancelled){throw cancel}
        catch(known:LocalAssetImportFailed){throw known}
        catch(failure:Exception){if(cancelled() && !committed) throw LocalAssetImportCancelled();throw LocalAssetImportFailed("LOCAL_ASSET_IMPORT_IO")}
        finally {
            // The operation holds the exclusive root lease. Cleanup is exact, owned and flat.
            runCatching {
                stage?.let {path -> val value=attributes(path)
                    if(value!=null && !value.isSymbolicLink && value.isRegularFile && value.size() in 0..spec.bytes) Files.delete(path)
                }
                if(attributes(namespace)!=null) reconcileOwned()
            }
        }
    }
}
