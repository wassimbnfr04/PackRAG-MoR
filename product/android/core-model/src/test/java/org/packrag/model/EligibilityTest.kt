package org.packrag.model

import org.junit.Assert.*
import org.junit.Test

class EligibilityTest {
    private val chunk = Chunk("c", "s", "title", "source", null, "Article 1", "text", "hash", "hash", 0,
        "MA", "2020-01-01", "2030-01-01", "2025-01-01", "2027-01-01", "active", "publisher", null, "en")
    @Test fun intersectionAndExclusiveEndBeforeSearch() {
        assertFalse(eligible(chunk, Query("q", "2024-12-31")))
        assertTrue(eligible(chunk, Query("q", "2025-01-01", "MA", true)))
        assertFalse(eligible(chunk, Query("q", "2027-01-01")))
        assertFalse(eligible(chunk, Query("q", "2026-01-01", "US")))
        assertFalse(eligible(chunk.copy(legalStatus = "repealed"), Query("q", "2026-01-01", "MA", true)))
        assertTrue(eligible(chunk.copy(legalStatus = "repealed"), Query("q", "2026-01-01", "MA", false)))
        assertTrue(eligible(chunk.copy(effectiveFrom = null, effectiveUntil = null), Query("q", "2020-01-01")))
        assertFalse(eligible(chunk.copy(effectiveFrom = null, effectiveUntil = null), Query("q", "2030-01-01")))
    }
}
