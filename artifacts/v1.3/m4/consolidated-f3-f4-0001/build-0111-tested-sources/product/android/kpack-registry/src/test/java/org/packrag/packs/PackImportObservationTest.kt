package org.packrag.packs

import java.io.File
import java.nio.file.Files
import java.util.zip.ZipFile
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.packrag.crypto.RawManifestVerifier as Crypto

class PackImportObservationTest {
    @Test fun actualCountsHaveIndependentByteDomainsAndZeroUnknownLength() {
        val events=mutableListOf<PackImportEvent>();val observation=PackImportObservation { events.add(it) }
        observation.checked(PackImportStage.SELECTED_DOCUMENT_COPY) { progress->progress(65_536);progress(85_076) }
        observation.checked(PackImportStage.PAYLOAD_INTEGRITY,21_565) { progress->progress(21_565) }
        assertEquals(85_076L,events.single { it.stage==PackImportStage.SELECTED_DOCUMENT_COPY && it.state==PackImportState.PASSED }.bytes)
        assertNull(events.first().totalBytes)
        assertEquals(21_565L,events.last().bytes);assertEquals(21_565L,events.last().totalBytes)
        events.clear();observation.checked(PackImportStage.SNAPSHOT_COPY) { }
        assertEquals(0L,events.last().bytes);assertNull(events.last().totalBytes)
    }
    @Test fun failedStageCannotPassOrAdvanceAndOriginalCauseIsRetained() {
        val events=mutableListOf<PackImportEvent>();val observation=PackImportObservation { events.add(it) }
        val cause=IllegalArgumentException("<b>attacker</b> /data/private/path")
        val rejected=assertThrows(PackImportRejected::class.java) {
            observation.checked(PackImportStage.PAYLOAD_INTEGRITY,10) { progress->progress(4);throw cause }
            observation.checked(PackImportStage.DATABASE_INDEX) { fail("Advanced after failure") }
        }
        assertEquals(PackImportFailure.PAYLOAD_REJECTED,rejected.category);assertSame(cause,rejected.cause)
        assertEquals("PAYLOAD_REJECTED",rejected.message)
        assertEquals(PackImportState.REJECTED,events.last().state);assertEquals(4L,events.last().bytes)
        assertFalse(events.any { it.state==PackImportState.PASSED || it.stage==PackImportStage.DATABASE_INDEX })
    }
    @Test fun throwingObserverCannotBypassChecksOrChangeSuccessfulReturn() {
        val observation=PackImportObservation { throw AssertionError("Observer is not a verifier") }
        var checked=false
        assertEquals(17,observation.checked(PackImportStage.ARCHIVE_AUDIT) { checked=true;17 })
        assertTrue(checked)
        val rejected=assertThrows(PackImportRejected::class.java) {
            observation.checked(PackImportStage.SIGNATURE_AUTHENTICATION) { throw IllegalArgumentException("bad signature") }
        }
        assertEquals(PackImportFailure.SIGNATURE_OR_MANIFEST_REJECTED,rejected.category)
    }
    @Test fun bytesCannotMoveBackwardsOrExceedKnownTotals() {
        for(values in listOf(listOf(4L,3L),listOf(11L))) {
            val rejected=assertThrows(PackImportRejected::class.java) {
                PackImportObservation().checked(PackImportStage.PAYLOAD_INTEGRITY,10) { progress->values.forEach(progress) }
            }
            assertEquals(PackImportFailure.PAYLOAD_REJECTED,rejected.category)
        }
        assertThrows(IllegalArgumentException::class.java) { PackImportEvent(PackImportStage.SNAPSHOT_COPY,PackImportState.PROGRESS,-1) }
    }
    @Test fun actualMalformedArchiveStopsBeforeSignatureAndCleansOnlyItsStage() {
        val root=Files.createTempDirectory("pack-import-contract-").toFile()
        try {
            val input=File(root,"bad.kpack");input.writeBytes(byteArrayOf(1,2,3));val before=Crypto.fileHash(input)
            val stage=File(root,"stage");val events=mutableListOf<PackImportEvent>()
            val rejected=assertThrows(PackImportRejected::class.java) {
                PackVerifier(listOf(ByteArray(32)),JSONObject(),"",true).stage(input,stage) { events.add(it) }
            }
            assertEquals(PackImportFailure.ARCHIVE_REJECTED,rejected.category)
            assertEquals(PackImportStage.ARCHIVE_AUDIT,events.last().stage);assertEquals(PackImportState.REJECTED,events.last().state)
            assertFalse(events.any { it.stage==PackImportStage.SIGNATURE_AUTHENTICATION });assertFalse(stage.exists())
            assertEquals(before,Crypto.fileHash(input))
        } finally { root.deleteRecursively() }
    }
    @Test fun actualSignedFixtureWithWrongPinnedKeyStopsBeforeManifestOrDatabase() {
        val repo=File(System.getProperty("packrag.repo"))
        val input=File(repo,"artifacts/v1.3/m1/smoke-0001/developer-pack/walking-skeleton.kpack")
        val profile=ZipFile(input).use { zip->JSONObject(zip.getInputStream(zip.getEntry("manifest.json")).readBytes().toString(Charsets.UTF_8)).getJSONObject("embedding_profile") }
        val root=Files.createTempDirectory("pack-import-signature-").toFile();val stage=File(root,"stage")
        val before=Crypto.fileHash(input);val events=mutableListOf<PackImportEvent>()
        try {
            val rejected=assertThrows(PackImportRejected::class.java) {
                PackVerifier(listOf(ByteArray(32)),profile,"",true).stage(input,stage) { events.add(it) }
            }
            assertEquals(PackImportFailure.SIGNATURE_OR_MANIFEST_REJECTED,rejected.category)
            assertTrue(rejected.cause!!.message!!.contains("Unknown signer or invalid signature"))
            assertEquals(PackImportStage.SIGNATURE_AUTHENTICATION,events.last().stage)
            assertFalse(events.any { it.stage in setOf(PackImportStage.MANIFEST_PROFILE_POLICY,PackImportStage.PAYLOAD_INTEGRITY,PackImportStage.DATABASE_INDEX) })
            assertFalse(stage.exists());assertEquals(before,Crypto.fileHash(input))
        } finally { root.deleteRecursively() }
    }
}
