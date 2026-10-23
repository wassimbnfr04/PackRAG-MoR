package org.packrag.packs

import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.abs
import kotlin.math.sqrt
import org.json.JSONObject
import org.packrag.crypto.RawManifestVerifier as Crypto

/** Independent structure checks precede SQLite; DB row hash binds afterward. */
object KdxFormat {
    fun inspect(file: File,profile: JSONObject,count: Int): String {
        require(count>=0 && file.length()==84L+count.toLong()*384*4) { "KDX count/size mismatch" }
        RandomAccessFile(file,"r").use { input ->
            val header=ByteArray(84); input.readFully(header)
            val buffer=ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN)
            val magic=ByteArray(8); buffer.get(magic)
            require(magic.contentEquals(byteArrayOf(75,68,88,49,0,0,0,0))) { "Invalid KDX header" }
            require(buffer.short.toInt()==1 && buffer.get().toInt()==1 && buffer.get().toInt()==1 && buffer.short.toInt()==384 && buffer.short.toInt()==1) { "Invalid KDX header" }
            require(buffer.int==count) { "KDX count/size mismatch" }
            val profileHash=ByteArray(32); buffer.get(profileHash)
            val mappingHash=ByteArray(32); buffer.get(mappingHash)
            require(Crypto.hex(profileHash)==Crypto.sha256(Crypto.canonical(profile.toString()))) { "KDX profile/mapping hash mismatch" }
            val vector=ByteArray(384*4)
            repeat(count) {
                input.readFully(vector); val values=ByteBuffer.wrap(vector).order(ByteOrder.LITTLE_ENDIAN); var norm=0.0
                repeat(384) { val value=values.float; require(value.isFinite()) { "Nonfinite KDX vector" }; norm+=value.toDouble()*value }
                require(abs(sqrt(norm)-1)<=.01) { "KDX vector norm mismatch" }
            }
            return Crypto.hex(mappingHash)
        }
    }
}
