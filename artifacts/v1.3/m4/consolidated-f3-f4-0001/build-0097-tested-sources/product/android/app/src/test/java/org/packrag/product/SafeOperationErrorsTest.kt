package org.packrag.product

import org.junit.Assert.*
import org.junit.Test
import org.packrag.packs.*

class SafeOperationErrorsTest {
    @Test fun arbitraryMessagesAndNestedCausesNeverReachProductLabels() {
        val hostile="<b>attacker</b> /data/user/0/private/key.seed32\n"+"x".repeat(5000)
        val cause=IllegalArgumentException(hostile)
        assertEquals("OPERATION_FAILED: The operation could not be completed. Check local files and installed packs before retrying.",safeOperationFailure(cause))
        for(code in PackImportFailure.entries) {
            val label=safeOperationFailure(PackImportRejected(code,cause))
            assertTrue(label.startsWith(code.name+":"));assertTrue(label.length<250)
            assertFalse(label.contains("attacker") || label.contains("/data/") || label.contains("seed32"))
        }
    }
    @Test fun uncertainCommitDoesNotClaimRollbackOrPriorFilePreservation() {
        val label=safeOperationFailure(PackImportRejected(PackImportFailure.REGISTRY_RECOVERY_REQUIRED,IllegalStateException("after commit")))
        assertTrue(label.contains("completion uncertain"));assertTrue(label.contains("rechecked installed state"))
        assertFalse(label.contains("Previous file retained") || label.contains("rolled back"))
    }
    @Test fun progressLabelsUseFixedStagesAndExplicitIndependentByteDomains() {
        assertEquals("Selected document copy (transport bytes): Completed · 21565 (total unknown) bytes",
            packImportEventLabel(PackImportEvent(PackImportStage.SELECTED_DOCUMENT_COPY,PackImportState.PASSED,21565)))
        assertEquals("Payload verification (uncompressed bytes): In progress · 65536 / 85076 bytes",
            packImportEventLabel(PackImportEvent(PackImportStage.PAYLOAD_INTEGRITY,PackImportState.PROGRESS,65536,85076)))
        assertEquals("Registry activation: Database committed; finishing activation",
            packImportEventLabel(PackImportEvent(PackImportStage.REGISTRY_COMMIT,PackImportState.COMMITTED)))
    }
    @Test fun queryFailureCodesAreAllowlistedAndUnknownTextIsDiscarded() {
        assertEquals("INVALID_QUERY_DATE",safeQueryInputCode(IllegalArgumentException("INVALID_QUERY_DATE")))
        assertEquals("INVALID_QUERY",safeQueryInputCode(IllegalArgumentException("/data/private/problem")))
    }
}
