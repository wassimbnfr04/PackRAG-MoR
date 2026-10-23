package org.packrag.product

import org.junit.Assert.*
import org.junit.Test

class ProductLayoutTest {
    private val id="8bdaf44d-76ee-4232-a8bc-81bfdc0b66d6"
    @Test fun onlyCanonicalIsolatedDebugIdentityCanSelectBoundedTestLayout() {
        assertEquals(ProductUiLayout(2f,320),isolatedUiLayout(true,id,2f,320))
        assertNull(isolatedUiLayout(false,id,2f,320))
        for(value in listOf(null,"../../owner","1-1-1-1-1",id.uppercase())) assertNull(isolatedUiLayout(true,value,2f,320))
    }
    @Test fun invalidOrUnboundedResourceOverridesAreIgnored() {
        for(scale in listOf(Float.NaN,Float.POSITIVE_INFINITY,-1f,0f,10f)) assertNull(isolatedUiLayout(true,id,scale,320))
        for(width in listOf(-1,0,1,10_000)) assertNull(isolatedUiLayout(true,id,2f,width))
        assertEquals(ProductUiLayout(1f,320),isolatedUiLayout(true,id,1f,320))
    }
}
