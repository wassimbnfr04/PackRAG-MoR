package org.packrag.model

import org.junit.Assert.*
import org.junit.Test

class FrozenEvidenceTest {
    private fun chunk()=Chunk(id="c",sourceId="s",title="title",sourceTitle="source",section=null,locator="locator",
        canonicalText="original",textSha256="a".repeat(64),originalSha256="b".repeat(64),denseRow=0,jurisdiction="MA",
        sourceFrom=null,sourceUntil=null,effectiveFrom=null,effectiveUntil=null,legalStatus="active",publisher="publisher",canonicalUri=null,language="en")
    @Test fun evidenceOwnsEveryNestedOriginConflictAndRelationshipList() {
        val members=mutableListOf("c");val retained=mutableListOf("c");val required=mutableListOf("b" to "a")
        val conflict=ConflictDecision(members,"RESOLVED","fixture",null,retained,required)
        val conflicts=mutableListOf(conflict)
        val relations=mutableListOf(SourceRelation("c","d","requires","fixture",1.0))
        val metadata=SourceMetadata(null,null,null,null,"key",relations)
        val derived=mutableListOf<DerivedText>()
        val identity=PackIdentity("pack","1.0.0","c".repeat(64));val origins=mutableListOf("origin")
        val records=mutableListOf(EvidenceOrigin(identity,chunk(),metadata,derived,true,1,1,.9,.03,
            CalibrationSnapshot("UNCALIBRATED",null,null),conflicts))
        val representation=GeneratorRepresentation("original","en","a".repeat(64),"canonical",null,null,null,"en","a".repeat(64))
        val frozen=FrozenEvidence(identity,chunk(),true,1,1,.9,.03,true,origins,records,conflicts,1,metadata,representation)
        members.clear();retained.clear();required.clear();conflicts.clear();relations.clear();origins.clear();records.clear()
        assertEquals(listOf("origin"),frozen.origins)
        assertEquals(listOf("c"),frozen.conflicts.single().members)
        assertEquals(listOf("b" to "a"),frozen.originRecords.single().conflicts.single().required)
        assertEquals("requires",frozen.originRecords.single().metadata.relations.single().relationType)
        assertEquals("original",frozen.chunk.canonicalText)
        assertThrows(UnsupportedOperationException::class.java) { (frozen.origins as MutableList).clear() }
        assertThrows(UnsupportedOperationException::class.java) { (frozen.conflicts.single().required as MutableList).clear() }
        assertThrows(UnsupportedOperationException::class.java) { (frozen.originRecords.single().metadata.relations as MutableList).clear() }
    }
}
