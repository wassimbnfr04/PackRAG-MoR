package org.packrag.product

import org.junit.Assert.*
import org.junit.Test
import org.packrag.model.PackIdentity
import org.packrag.model.PackOverview

class PackOverviewPresentationTest {
    private val identity=PackIdentity("org.packrag.development.walking-skeleton","0.1.0","a".repeat(64))
    private val overview=PackOverview(identity,"Synthetic v1.3 development pack","PackRAG DEVELOPMENT ONLY",
        "ed25519:5148c71b861624fabbcd4a5a9e0a2804963fd7132119ca4cd375677e445b5081","2027-01-01",2586,85076,21565)
    private fun row(active:Boolean=true)=PackRow(identity.packId,identity.version,identity.manifestSha256,"VERIFIED",active,null,null,overview)

    @Test fun signedFixtureByteDomainsAndPublisherFieldsRemainDistinct() {
        val lines=packOverviewLines(row(),"2026-12-31")
        assertTrue(lines.contains("Publisher: PackRAG DEVELOPMENT ONLY"))
        assertTrue(lines.contains("Publisher public key ID: ed25519:5148c71b861624fabbcd4a5a9e0a2804963fd7132119ca4cd375677e445b5081"))
        assertTrue(lines.contains("Version: 0.1.0"))
        assertTrue(lines.contains("Manifest bytes (signed JSON): 2586"))
        assertTrue(lines.contains("Payload bytes (uncompressed): 85076"))
        assertTrue(lines.contains("Transport bytes (KPack archive): 21565"))
        assertTrue(lines.contains("Manifest SHA256: "+"a".repeat(64)))
    }
    @Test fun storedLabelCannotAuthenticateAbsentOverview() {
        val missing=row().copy(overview=null)
        assertNull(authenticatedOverview(missing))
        assertEquals(1,packOverviewLines(missing,"2026-12-31").size)
        assertTrue(packOverviewLines(missing,"2026-12-31").single().startsWith("Metadata unavailable:"))
        assertEquals("Active · metadata verification unavailable",packVerificationLabel(missing))
        assertFalse(packOverviewLines(missing,"2026-12-31").single().contains("DEVELOPMENT ONLY"))
        assertEquals("Stored install trust: unavailable.",storedPackTrustLabel("/data/private/attacker-text"))
    }
    @Test fun mismatchedIdVersionOrHashNeverBorrowsVerifiedFields() {
        for(wrong in listOf(row().copy(id="org.other.pack"),row().copy(version="1.0.0"),row().copy(hash="b".repeat(64)))) {
            assertNull(authenticatedOverview(wrong))
            assertEquals("Active · metadata verification unavailable",packVerificationLabel(wrong))
            assertFalse(packOverviewLines(wrong,"2026-12-31").any { it.startsWith("Publisher:") || it.startsWith("Payload bytes") })
        }
    }
    @Test fun renderedAdvisoryIsInclusiveAndCannotEditSubmittedContext() {
        val captured=SubmittedQuery(submittedQuery("original question","2028-02-29","MA-01",true),listOf(PackFreshness(identity,"2027-01-01")))
        assertTrue(packOverviewLines(row(),"2026-12-31").any { it.endsWith("not due") })
        for(date in listOf("2027-01-01","2027-01-02"))assertTrue(packOverviewLines(row(),date).any { it.contains("advisory due; evidence remains subject to normal validation") })
        assertEquals("2028-02-29",captured.query.asOf);assertEquals("MA-01",captured.query.jurisdiction)
        assertEquals("original question",captured.query.raw)
    }
    @Test fun activeNavigationOwnsExactDistinctIdentitiesAndIgnoresInactiveVersions() {
        val older=row(false).copy(version="0.0.9",hash="b".repeat(64),overview=null)
        val other=row().copy(id="org.other.pack",hash="c".repeat(64),overview=null)
        val input=mutableListOf(older,row(),other)
        val selected=activePackIdentities(input);input.clear()
        assertEquals(listOf(identity,PackIdentity("org.other.pack","0.1.0","c".repeat(64))),selected)
        assertTrue(activePackIdentities(emptyList()).isEmpty())
        assertEquals(listOf(identity),activePackIdentities(listOf(row())))
        try { (selected as MutableList).clear();fail("Navigation identities mutable") } catch(expected:UnsupportedOperationException) { }
    }
    @Test fun literalLongTextAndIndependentNonnegativeSizesDoNotAggregateOrOverflow() {
        val text="Publisher <b>literal</b>\n"+"أ".repeat(500)
        val value=overview.copy(publisherName=text,manifestBytes=Long.MAX_VALUE,payloadBytes=0,transportBytes=Long.MAX_VALUE)
        val lines=packOverviewLines(row().copy(overview=value),"2027-01-01")
        assertTrue(lines.contains("Publisher: $text"));assertTrue(lines.contains("Payload bytes (uncompressed): 0"))
        assertTrue(lines.contains("Transport bytes (KPack archive): 9223372036854775807"))
        assertThrows(IllegalArgumentException::class.java) { overview.copy(manifestBytes=-1) }
        assertThrows(java.time.DateTimeException::class.java) { overview.copy(updateCheckAfter="2027-02-29") }
    }
}
