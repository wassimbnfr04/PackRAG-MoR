package org.packrag.generator

import org.junit.Assert.*
import org.junit.Test

class NativeEmissionContractTest {
    @Test fun nativeAbiResultImplementsGenericOwnershipWithoutReasoningInDiagnostics() {
        val raw="<think>PRIVATE_REASONING_SENTINEL</think>final".toByteArray()
        val ids=intArrayOf(4,7,9)
        val result: GenerationResult=NativeEmission(raw,ids,2,1.0,2.0,3.0,4.0)
        assertSame(raw,result.buffer); assertSame(ids,result.emitted)
        assertFalse(result.toString().contains("SENTINEL")); assertFalse(result.toString().contains("final"))
        assertEquals(2,result.stop); assertEquals(1.0,result.prefillMs,0.0); assertEquals(2.0,result.decodeWallMs,0.0)
        assertEquals(3.0,result.firstEmittedTokenMs,0.0); assertEquals(4.0,result.totalMs,0.0)
        result.buffer.fill(0); assertTrue(raw.all { it==0.toByte() })
    }
}
