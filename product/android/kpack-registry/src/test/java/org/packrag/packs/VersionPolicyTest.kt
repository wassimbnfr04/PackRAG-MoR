package org.packrag.packs

import org.junit.Assert.*
import org.junit.Test

class VersionPolicyTest {
    @Test fun olderAndEqualPrecedenceRequireAcknowledgment() {
        assertFalse(VersionPolicy.needsWarning("1.0.0",null))
        assertFalse(VersionPolicy.needsWarning("1.0.10","1.0.9"))
        for(version in listOf("0.9.0","1.0.0","1.0.0+different")) {
            assertTrue(VersionPolicy.needsWarning(version,"1.0.0"))
            assertThrows(IllegalArgumentException::class.java) { VersionPolicy.requireAcknowledgment(version,"1.0.0",false) }
            VersionPolicy.requireAcknowledgment(version,"1.0.0",true)
        }
    }
    @Test fun immutableIdentityAndNumericPrecedence() {
        VersionPolicy.newInstall("1.0.0",false,null)
        VersionPolicy.newInstall("1.0.10",false,"1.0.9")
        VersionPolicy.newInstall("1.0.0",false,"1.0.0-rc.10")
        VersionPolicy.newInstall("1.0.0-rc.10",false,"1.0.0-rc.9")
        for((candidate,highest,installed) in listOf(Triple("1.0.0","1.0.0",false),Triple("1.0.0+new","1.0.0+old",false),Triple("0.9.0","1.0.0",false),Triple("1.0.0-rc.1","1.0.0",false),Triple("2.0.0","1.0.0",true)))
            assertThrows(IllegalArgumentException::class.java) { VersionPolicy.newInstall(candidate,installed,highest) }
    }
}
