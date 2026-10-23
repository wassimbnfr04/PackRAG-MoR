package org.packrag.product

import java.io.File
import java.io.InputStream
import java.nio.channels.Channels
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.Path
import java.nio.file.StandardOpenOption
import java.nio.file.NoSuchFileException
import java.nio.file.attribute.BasicFileAttributes
import java.security.MessageDigest
import java.time.Instant

/** These are the existing four private assets, not caller-selected destinations. */
enum class LocalAssetSlot(val relativePath:String,val label:String,val expectedBytes:Long,val expectedSha256:String) {
    GENERATOR("LFM2.5-2.6B-QAD-Q4_0.gguf","LFM2.5 generator",1593894944L,"a247afd6414918eac8e520a9e6137dc271235461ecbe1180462221d5b8d40b03"),
    TEMPLATE("chat_template.jinja","Official chat template",5443L,"ea663864491de7ade391839479860ca95541f892f72665c73251fbd4643b1bef"),
    TOKENIZER("granite/tokenizer.json","Granite tokenizer",25301672L,"4f2842d568e2724370aec203652a42ac783c7937f8347a1a2cc7506d71f1582f"),
    ENCODER("granite/onnx/model.onnx","Granite encoder",390004608L,"68e592b160673d30250824c1116bc6ab33f70efb22b97c9e1d7ce1e69c1c9d70")
}

/** Smaller independently pinned specimens are allowed in verifier unit tests only. */
data class LocalAssetSpec(val slot:LocalAssetSlot,val bytes:Long=slot.expectedBytes,val sha256:String=slot.expectedSha256) {
    init { require(bytes in 1..slot.expectedBytes && sha256.matches(Regex("[0-9a-f]{64}"))) }
}
enum class LocalAssetCondition { UNCHECKED,MISSING,WRONG_SIZE,CORRUPT,UNREADABLE,UNSAFE_PATH,VERIFIED }
data class LocalAssetStatus(val spec:LocalAssetSpec,val condition:LocalAssetCondition=LocalAssetCondition.UNCHECKED,
    val observedBytes:Long?=null,val observedSha256:String?=null,val checkedAt:String?=null)
class LocalAssetCheckCancelled:RuntimeException("LOCAL_ASSET_CHECK_CANCELLED")
class LocalAssetsUnavailable(val statuses:List<LocalAssetStatus>):IllegalStateException(
    statuses.first { it.condition!=LocalAssetCondition.VERIFIED }.let {
        "LOCAL_ASSET_${it.condition}: ${it.spec.slot.relativePath}. Open Local assets, check files and install the pinned artifact."
    })

/** Read-only; no model initialization, writes, URI access or following asset symlinks. */
class LocalAssetVerifier(private val root:File,
    private val specs:List<LocalAssetSpec> = LocalAssetSlot.entries.map { LocalAssetSpec(it) },
    private val openInput:(Path)->InputStream = { path ->
        Channels.newInputStream(Files.newByteChannel(path,setOf(StandardOpenOption.READ,LinkOption.NOFOLLOW_LINKS)))
    }) {
    init { require(specs.isNotEmpty() && specs.map { it.slot }.distinct().size==specs.size) }
    fun unchecked():List<LocalAssetStatus> = specs.map { LocalAssetStatus(it) }
    fun verify(cancelled:()->Boolean = { false }):List<LocalAssetStatus> = specs.map { check(it,cancelled) }
    private fun check(spec:LocalAssetSpec,cancelled:()->Boolean):LocalAssetStatus {
        fun result(condition:LocalAssetCondition,bytes:Long?=null,sha:String?=null)=
            LocalAssetStatus(spec,condition,bytes,sha,Instant.now().toString())
        if(cancelled()) throw LocalAssetCheckCancelled()
        try {
            var path=root.toPath().toAbsolutePath().normalize()
            val rootAttributes=Files.readAttributes(path,BasicFileAttributes::class.java,LinkOption.NOFOLLOW_LINKS)
            if(rootAttributes.isSymbolicLink || !rootAttributes.isDirectory) return result(LocalAssetCondition.UNSAFE_PATH)
            val pieces=spec.slot.relativePath.split('/')
            var attributes=rootAttributes
            for((index,piece) in pieces.withIndex()) {
                path=path.resolve(piece)
                attributes=Files.readAttributes(path,BasicFileAttributes::class.java,LinkOption.NOFOLLOW_LINKS)
                if(attributes.isSymbolicLink) return result(LocalAssetCondition.UNSAFE_PATH)
                if(index<pieces.lastIndex && !attributes.isDirectory) return result(LocalAssetCondition.UNSAFE_PATH)
            }
            if(!attributes.isRegularFile) return result(LocalAssetCondition.UNSAFE_PATH)
            val announced=attributes.size()
            if(announced!=spec.bytes) return result(LocalAssetCondition.WRONG_SIZE,announced)
            val digest=MessageDigest.getInstance("SHA-256")
            var bytes=0L
            openInput(path).use { input ->
                val buffer=ByteArray(65536)
                while(true) {
                    if(cancelled()) throw LocalAssetCheckCancelled()
                    val count=input.read(buffer)
                    if(count<0) break
                    if(count==0) {
                        val one=input.read()
                        if(one<0) break
                        bytes++
                        if(bytes>spec.bytes) return result(LocalAssetCondition.WRONG_SIZE,bytes)
                        digest.update(one.toByte())
                    } else {
                        bytes+=count
                        if(bytes>spec.bytes) return result(LocalAssetCondition.WRONG_SIZE,bytes)
                        digest.update(buffer,0,count)
                    }
                }
            }
            if(cancelled()) throw LocalAssetCheckCancelled()
            if(bytes!=spec.bytes) return result(LocalAssetCondition.WRONG_SIZE,bytes)
            val observed=digest.digest().joinToString("") { (it.toInt() and 255).toString(16).padStart(2,'0') }
            return result(if(observed==spec.sha256) LocalAssetCondition.VERIFIED else LocalAssetCondition.CORRUPT,bytes,observed)
        } catch(cancel:LocalAssetCheckCancelled) { throw cancel }
        catch(missing:NoSuchFileException) { return result(LocalAssetCondition.MISSING) }
        catch(failure:Exception) { return result(LocalAssetCondition.UNREADABLE) }
    }
}

fun localAssetGuidance(condition:LocalAssetCondition):String = when(condition) {
    LocalAssetCondition.UNCHECKED -> "Configured; files have not been checked in this session."
    LocalAssetCondition.MISSING -> "Missing. Install the exact pinned file in this slot."
    LocalAssetCondition.WRONG_SIZE -> "Wrong size or truncated file. Use the complete pinned artifact."
    LocalAssetCondition.CORRUPT -> "Hash mismatch. Use the exact pinned artifact."
    LocalAssetCondition.UNREADABLE -> "The file could not be read. Check local storage and retry."
    LocalAssetCondition.UNSAFE_PATH -> "Unsafe path or non-file entry. Use a regular private asset file."
    LocalAssetCondition.VERIFIED -> "Exact size and SHA256 matched at the last completed check."
}
