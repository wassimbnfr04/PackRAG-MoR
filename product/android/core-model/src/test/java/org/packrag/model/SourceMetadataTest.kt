package org.packrag.model

import org.junit.Assert.*
import org.junit.Test

class SourceMetadataTest {
    @Test fun signedFieldsRemainOriginalAndIncomingOutgoingEdgesAreExposedWithoutExpansion() {
        val chunk=Chunk("c","s","title","source",null,"locator","text","hash","hash",0,null,null,null,null,null,null,"publisher",null,"en",
            Int.MAX_VALUE,"نسخة révision","2026-01-01T00:00:00.125Z","𝟙37")
        val outgoing=SourceRelation("c","target","amends","explicit-reference",.75)
        val incoming=SourceRelation("other","c","exception_to","curated",0.0)
        val irrelevant=SourceRelation("other","target","cites","structure",1.0)
        val metadata=sourceMetadata(chunk,"approved-publisher-id",listOf(outgoing,incoming,irrelevant))
        assertEquals(Int.MAX_VALUE,metadata.authorityRank);assertEquals("نسخة révision",metadata.documentVersion)
        assertEquals("2026-01-01T00:00:00.125Z",metadata.issuedAt);assertEquals("𝟙37",metadata.article)
        assertEquals("approved-publisher-id",metadata.publisherKeyId);assertEquals(listOf(outgoing,incoming),metadata.relations)
        val unknown=sourceMetadata(chunk.copy(authorityRank=null,documentVersion=null,issuedAt=null,article=null),"id",emptyList())
        assertNull(unknown.authorityRank);assertNull(unknown.documentVersion);assertNull(unknown.issuedAt);assertNull(unknown.article)
        assertTrue(unknown.relations.isEmpty())
        val empty=sourceMetadata(chunk.copy(documentVersion="",article="",authorityRank=0),"id",emptyList())
        assertEquals("",empty.documentVersion);assertEquals("",empty.article);assertEquals(0,empty.authorityRank)
    }
}
