package org.packrag.generator

import org.junit.Assert.assertThrows
import org.junit.Test

class GeneratorIdentityTest {
    @Test fun identitiesCannotCarryMalformedModelOrTemplateHashes() {
        for (bad in listOf("", "a".repeat(63), "A".repeat(64), "g".repeat(64))) {
            assertThrows(IllegalArgumentException::class.java) { GeneratorIdentity(bad,"b".repeat(64),"revision","backend") }
            assertThrows(IllegalArgumentException::class.java) { GeneratorIdentity("a".repeat(64),bad,"revision","backend") }
            assertThrows(IllegalArgumentException::class.java) { GeneratorIdentity("a".repeat(64),"b".repeat(64),"revision","backend",bad) }
        }
        assertThrows(IllegalArgumentException::class.java) { GeneratorIdentity("a".repeat(64),"b".repeat(64)," ","backend") }
        assertThrows(IllegalArgumentException::class.java) { GeneratorIdentity("a".repeat(64),"b".repeat(64),"revision"," ") }
    }
}
