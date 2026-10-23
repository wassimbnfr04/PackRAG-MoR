package org.packrag.model

import org.junit.Assert.*
import org.junit.Test

class PortableNamesTest {
    @Test fun fullFoldingAndCodepointOrdering() {
        assertEquals("15.0.0",PortableNames.UNICODE_VERSION)
        assertEquals("ssσffi\u0307",PortableNames.fold("ßςﬀİ"))
        assertNotEquals(PortableNames.fold("ı"),PortableNames.fold("i"))
        assertEquals(listOf("\ue000","😀"),listOf("😀","\ue000").sortedWith(PortableNames.order))
        assertEquals("𐐨",PortableNames.fold("𐐀"))
    }
}
