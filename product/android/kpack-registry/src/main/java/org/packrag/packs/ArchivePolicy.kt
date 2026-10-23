package org.packrag.packs

import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.text.Normalizer
import java.util.Locale
import java.util.zip.CRC32
import org.packrag.model.PortableNames

/** Bounded classic central directory; small forced-ZIP64 local records allowed. */
object ArchivePolicy {
    const val MAX_ENTRY = 256L * 1024 * 1024
    const val MAX_TOTAL = 512L * 1024 * 1024
    const val MAX_TRANSPORT = MAX_TOTAL + 1024 * 1024
    val controls = setOf("manifest.json", "manifest.sig")
    private val sourceTypes = mapOf(
        "txt" to "text/plain", "md" to "text/markdown", "pdf" to "application/pdf",
        "csv" to "text/csv", "tsv" to "text/tab-separated-values", "json" to "application/json",
        "xml" to "application/xml", "png" to "image/png", "jpg" to "image/jpeg",
        "jpeg" to "image/jpeg", "webp" to "image/webp"
    )
    fun allowedMediaType(path: String, mediaType: String) {
        safePath(path)
        val expected = if (path.startsWith("sources/")) sourceTypes.getValue(File(path).extension.lowercase(Locale.ROOT))
            else when(path) { "knowledge.sqlite" -> "application/vnd.sqlite3"; "dense.kdx" -> "application/octet-stream"; else -> null }
        require(mediaType.lowercase(Locale.ROOT) in setOf(expected,"application/octet-stream")) { "Payload media type not allow-listed" }
    }
    fun safePath(path: String) {
        require(path.isNotEmpty() && !path.startsWith('/') && '\\' !in path && ':' !in path)
        require(Normalizer.normalize(path, Normalizer.Form.NFC) == path && path.toByteArray(Charsets.UTF_8).size <= 4096)
        for (part in path.split('/')) {
            require(part !in listOf("", ".", "..") && !part.endsWith('.') && !part.endsWith(' ') && part.toByteArray(Charsets.UTF_8).size <= 255)
            require(part.none { it.code < 32 || it.code == 127 || it in "<>\"|?*" })
            require(!Regex("(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\\..*)?").matches(part))
        }
        require(path in controls || path in setOf("knowledge.sqlite", "dense.kdx") || path.startsWith("sources/"))
        if (path.startsWith("sources/")) require(File(path).extension.lowercase(Locale.ROOT) in sourceTypes) { "Source data type not allow-listed" }
    }
    private fun u16(bytes: ByteArray, at: Int) = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).getShort(at).toInt() and 65535
    private fun u32(bytes: ByteArray, at: Int) = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).getInt(at).toLong() and 0xffffffffL
    private fun u64(bytes: ByteArray, at: Int): Long {
        require(at + 8 <= bytes.size)
        return ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).getLong(at).also { require(it >= 0) }
    }
    private fun extras(bytes: ByteArray, name: ByteArray): Map<Int,ByteArray> {
        val result = mutableMapOf<Int,ByteArray>(); var at = 0
        while(at < bytes.size) {
            require(at + 4 <= bytes.size); val tag = u16(bytes,at); val size = u16(bytes,at+2); at += 4
            require(at + size <= bytes.size && tag !in result)
            result[tag] = bytes.copyOfRange(at,at+size); at += size
        }
        require(0x0017 !in result && 0x9901 !in result)
        result[0x7075]?.let { value ->
            val crc = CRC32().apply { update(name) }.value
            require(value.size >= 5 && value[0].toInt() == 1 && u32(value,1) == crc && value.copyOfRange(5,value.size).contentEquals(name)) { "Ambiguous Unicode ZIP name" }
        }
        return result
    }
    private data class Entry(val name: String, val raw: ByteArray, val version: Int, val flags: Int, val method: Int, val crc: Long, val compressed: Long, val size: Long, val local: Long)
    fun audit(file: File) {
        RandomAccessFile(file,"r").use { input ->
            val length = input.length(); require(length in 22..MAX_TRANSPORT)
            fun read(offset: Long, count: Int, end: Long = length): ByteArray {
                require(offset in 0..end && count >= 0 && count.toLong() <= end-offset) { "ZIP record outside bounds" }
                return ByteArray(count).also { input.seek(offset); input.readFully(it) }
            }
            val tailOffset = maxOf(0L,length-65557); val tail = read(tailOffset,(length-tailOffset).toInt())
            val ends = (tail.size-22 downTo 0).filter { u32(tail,it) == 0x06054b50L && it+22+u16(tail,it+20) == tail.size }
            require(ends.size == 1); val endIndex = ends.single(); val end = tailOffset+endIndex
            val count = u16(tail,endIndex+10); val cdLength = u32(tail,endIndex+12); val cdOffset = u32(tail,endIndex+16)
            require(u16(tail,endIndex+4) == 0 && u16(tail,endIndex+6) == 0 && u16(tail,endIndex+8) == count && count in 2..5000 && cdOffset+cdLength == end)
            var offset = cdOffset; var total = 0L; val entries = mutableListOf<Entry>(); val seen = mutableSetOf<String>()
            repeat(count) {
                val fixed = read(offset,46,end); require(u32(fixed,0) == 0x02014b50L)
                val version = u16(fixed,6); val flags = u16(fixed,8); val method = u16(fixed,10)
                val crc = u32(fixed,16); val compressed = u32(fixed,20); val size = u32(fixed,24)
                val nl = u16(fixed,28); val el = u16(fixed,30); val cl = u16(fixed,32); val attrs = u32(fixed,38)
                require(version in setOf(10,20,45) && flags and 0x080E.inv() == 0 && method in setOf(0,8) && (method != 0 || flags and 6 == 0))
                require(u16(fixed,34) == 0 && ((attrs ushr 16).toInt() and 0xf000) in setOf(0,0x8000) && attrs and 0x10L == 0L)
                require(size <= MAX_ENTRY && compressed <= MAX_TRANSPORT && (method != 0 || compressed == size))
                total += size; require(total <= MAX_TOTAL)
                val name = read(offset+46,nl,end); val path = name.toString(Charsets.UTF_8)
                require(path.toByteArray(Charsets.UTF_8).contentEquals(name) && (flags and 0x800 != 0 || name.all { it >= 0 }))
                safePath(path); require(seen.add(PortableNames.fold(path))) { "Duplicate ZIP name" }
                require(1 !in extras(read(offset+46+nl,el,end),name))
                entries.add(Entry(path,name,version,flags,method,crc,compressed,size,u32(fixed,42)))
                offset += 46+nl+el+cl; require(offset <= end)
            }
            require(offset == end && entries.map { it.name }.containsAll(controls))
            require(entries.single { it.name == "manifest.json" }.size <= 1024*1024 && entries.single { it.name == "manifest.sig" }.size == 64L)
            var cursor = 0L
            for(entry in entries.sortedBy { it.local }) {
                require(entry.local == cursor) { "Overlapping/hidden ZIP local records" }
                val fixed = read(cursor,30,cdOffset); require(u32(fixed,0) == 0x04034b50L)
                val version = u16(fixed,4); val flags = u16(fixed,6); val method = u16(fixed,8)
                val crc = u32(fixed,14); var compressed = u32(fixed,18); var size = u32(fixed,22)
                val nl = u16(fixed,26); val el = u16(fixed,28)
                require(version == entry.version && flags == entry.flags && method == entry.method)
                val name = read(cursor+30,nl,cdOffset); require(name.contentEquals(entry.raw)) { "Local/central name mismatch" }
                val extra = extras(read(cursor+30+nl,el,cdOffset),name); val zip64 = compressed == 0xffffffffL || size == 0xffffffffL
                if(zip64) {
                    require(version == 45 && 1 in extra); val values = extra.getValue(1); var position = 0
                    if(size == 0xffffffffL) { size = u64(values,position); position += 8 }
                    if(compressed == 0xffffffffL) { compressed = u64(values,position); position += 8 }
                    require(position == values.size)
                } else require(1 !in extra)
                if(flags and 8 != 0) require(crc in setOf(0L,entry.crc) && compressed in setOf(0L,entry.compressed) && size in setOf(0L,entry.size))
                else require(crc == entry.crc && compressed == entry.compressed && size == entry.size)
                cursor += 30+nl+el+entry.compressed; require(cursor <= cdOffset)
                if(flags and 8 != 0) {
                    if(u32(read(cursor,4,cdOffset),0) == 0x08074b50L) cursor += 4
                    val descriptor = read(cursor,if(zip64) 20 else 12,cdOffset)
                    require(u32(descriptor,0) == entry.crc && (if(zip64) u64(descriptor,4) else u32(descriptor,4)) == entry.compressed && (if(zip64) u64(descriptor,12) else u32(descriptor,8)) == entry.size)
                    cursor += descriptor.size
                }
            }
            require(cursor == cdOffset) { "Hidden ZIP data before central directory" }
        }
    }
}
