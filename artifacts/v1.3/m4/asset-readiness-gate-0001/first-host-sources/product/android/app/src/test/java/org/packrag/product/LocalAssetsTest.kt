package org.packrag.product

import java.io.ByteArrayInputStream
import java.io.File
import java.io.IOException
import java.nio.file.Files
import java.util.concurrent.atomic.AtomicBoolean
import org.junit.Assert.*
import org.junit.Test

class LocalAssetsTest {
    private val hello="hello".toByteArray(Charsets.UTF_8)
    private val helloSha="2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    private val worldSha="486ea46224d1bb4fb680f34f7c9ad96a8f24ec88be73ea8e5a6c65260e9cb8a7"
    private fun fixture(action:(File,LocalAssetSpec)->Unit) {
        val root=Files.createTempDirectory("packrag-asset-test-").toFile()
        try { action(root,LocalAssetSpec(LocalAssetSlot.TEMPLATE,5,helloSha)) }
        finally { root.deleteRecursively() }
    }
    @Test fun productionSlotsHaveIndependentExactPathsBoundsAndPins() {
        assertEquals(listOf("LFM2.5-2.6B-QAD-Q4_0.gguf","chat_template.jinja","granite/tokenizer.json","granite/onnx/model.onnx"),LocalAssetSlot.entries.map { it.relativePath })
        assertEquals(listOf(1593894944L,5443L,25301672L,390004608L),LocalAssetSlot.entries.map { it.expectedBytes })
        assertEquals("a247afd6414918eac8e520a9e6137dc271235461ecbe1180462221d5b8d40b03",LocalAssetSlot.GENERATOR.expectedSha256)
        assertEquals("ea663864491de7ade391839479860ca95541f892f72665c73251fbd4643b1bef",LocalAssetSlot.TEMPLATE.expectedSha256)
        assertEquals("4f2842d568e2724370aec203652a42ac783c7937f8347a1a2cc7506d71f1582f",LocalAssetSlot.TOKENIZER.expectedSha256)
        assertEquals("68e592b160673d30250824c1116bc6ab33f70efb22b97c9e1d7ce1e69c1c9d70",LocalAssetSlot.ENCODER.expectedSha256)
        assertThrows(IllegalArgumentException::class.java) { LocalAssetSpec(LocalAssetSlot.TEMPLATE,0,helloSha) }
        assertThrows(IllegalArgumentException::class.java) { LocalAssetSpec(LocalAssetSlot.TEMPLATE,5444,helloSha) }
        assertThrows(IllegalArgumentException::class.java) { LocalAssetSpec(LocalAssetSlot.TEMPLATE,5,helloSha.uppercase()) }
        fixture { root,spec -> assertThrows(IllegalArgumentException::class.java) { LocalAssetVerifier(root,listOf(spec,spec)) } }
    }
    @Test fun uncheckedAndMissingNeverClaimZeroOrReadBytes() = fixture { root,spec ->
        var opened=0
        val verifier=LocalAssetVerifier(root,listOf(spec)) { opened++;throw AssertionError("Must not open a missing file") }
        val unchecked=verifier.unchecked().single()
        assertEquals(LocalAssetCondition.UNCHECKED,unchecked.condition);assertNull(unchecked.checkedAt);assertNull(unchecked.observedBytes)
        val missing=verifier.verify().single()
        assertEquals(LocalAssetCondition.MISSING,missing.condition);assertNull(missing.observedBytes);assertEquals(0,opened)
    }
    @Test fun emptyTruncatedAndOversizedRejectBeforeHashing() = fixture { root,spec ->
        for(bytes in listOf(byteArrayOf(),byteArrayOf(1,2),ByteArray(6))) {
            File(root,spec.slot.relativePath).writeBytes(bytes)
            val status=LocalAssetVerifier(root,listOf(spec)) { throw AssertionError("Wrong size must reject before input open") }.verify().single()
            assertEquals(LocalAssetCondition.WRONG_SIZE,status.condition);assertEquals(bytes.size.toLong(),status.observedBytes)
            assertNull(status.observedSha256)
        }
    }
    @Test fun exactBytesVerifyAndSameSizeWrongSlotBytesReject() = fixture { root,spec ->
        val file=File(root,spec.slot.relativePath);file.writeBytes(hello)
        val positive=LocalAssetVerifier(root,listOf(spec)).verify().single()
        assertEquals(LocalAssetCondition.VERIFIED,positive.condition);assertEquals(helloSha,positive.observedSha256);assertEquals(5L,positive.observedBytes)
        assertArrayEquals(hello,file.readBytes())
        file.writeText("world",Charsets.UTF_8)
        val corrupt=LocalAssetVerifier(root,listOf(spec)).verify().single()
        assertEquals(LocalAssetCondition.CORRUPT,corrupt.condition);assertEquals(worldSha,corrupt.observedSha256)
        file.writeBytes(hello)
        val wrongSlot=LocalAssetVerifier(root,listOf(LocalAssetSpec(LocalAssetSlot.TEMPLATE,5,worldSha))).verify().single()
        assertEquals(LocalAssetCondition.CORRUPT,wrongSlot.condition)
    }
    @Test fun directoriesAndNonDirectoryParentsRejectWithoutInput() = fixture { root,spec ->
        assertTrue(File(root,spec.slot.relativePath).mkdir())
        val directory=LocalAssetVerifier(root,listOf(spec)) { throw AssertionError("Must not read a directory") }.verify().single()
        assertEquals(LocalAssetCondition.UNSAFE_PATH,directory.condition)
        File(root,"granite").writeBytes(hello)
        val invalidParent=LocalAssetVerifier(root,listOf(LocalAssetSpec(LocalAssetSlot.TOKENIZER,5,helloSha))) { throw AssertionError("Must not traverse a file parent") }.verify().single()
        assertEquals(LocalAssetCondition.UNSAFE_PATH,invalidParent.condition)
    }
    @Test fun readErrorsDoNotExposeUnderlyingExceptionOrVerify() = fixture { root,spec ->
        File(root,spec.slot.relativePath).writeBytes(hello)
        val status=LocalAssetVerifier(root,listOf(spec)) { throw IOException("Untrusted internal path must stay out of guidance") }.verify().single()
        assertEquals(LocalAssetCondition.UNREADABLE,status.condition);assertNull(status.observedSha256)
        val error=LocalAssetsUnavailable(listOf(status))
        assertTrue(error.message!!.contains("LOCAL_ASSET_UNREADABLE"));assertFalse(error.message!!.contains("Untrusted internal"))
    }
    @Test fun changingInputLengthIsMeasuredNotTrustedFromMetadata() = fixture { root,spec ->
        val file=File(root,spec.slot.relativePath);file.writeBytes(hello)
        for(bytes in listOf(byteArrayOf(1,2),ByteArray(6))) {
            val status=LocalAssetVerifier(root,listOf(spec)) { ByteArrayInputStream(bytes) }.verify().single()
            assertEquals(LocalAssetCondition.WRONG_SIZE,status.condition);assertEquals(bytes.size.toLong(),status.observedBytes)
            assertArrayEquals(hello,file.readBytes())
        }
    }
    @Test fun shortAndZeroReadsStillHashAllActualBytes() = fixture { root,spec ->
        File(root,spec.slot.relativePath).writeBytes(hello)
        val status=LocalAssetVerifier(root,listOf(spec)) {
            object:ByteArrayInputStream(hello) {
                var first=true
                override fun read(bytes:ByteArray,offset:Int,length:Int):Int {
                    if(first) { first=false;return 0 }
                    return super.read(bytes,offset,minOf(length,2))
                }
            }
        }.verify().single()
        assertEquals(LocalAssetCondition.VERIFIED,status.condition);assertEquals(helloSha,status.observedSha256)
    }
    @Test fun cancellationDuringStreamingClosesInputAndPreservesFile() = fixture { root,spec ->
        val file=File(root,spec.slot.relativePath);file.writeBytes(hello)
        val cancelled=AtomicBoolean(false);val closed=AtomicBoolean(false)
        val verifier=LocalAssetVerifier(root,listOf(spec)) {
            object:ByteArrayInputStream(hello) {
                override fun read(bytes:ByteArray,offset:Int,length:Int):Int {
                    val count=super.read(bytes,offset,minOf(length,2));cancelled.set(true);return count
                }
                override fun close() { closed.set(true);super.close() }
            }
        }
        assertThrows(LocalAssetCheckCancelled::class.java) { verifier.verify { cancelled.get() } }
        assertTrue(closed.get());assertArrayEquals(hello,file.readBytes())
    }
}
