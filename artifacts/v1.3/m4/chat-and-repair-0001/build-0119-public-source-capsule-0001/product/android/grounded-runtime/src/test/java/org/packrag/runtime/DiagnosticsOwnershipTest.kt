package org.packrag.runtime

import org.junit.Assert.*
import org.junit.Test
import org.packrag.model.*

class DiagnosticsOwnershipTest {
    @Test fun diagnosticOriginsAndPoolsOutliveMutableInputs() {
        val chunk=Chunk("c","s","title","source",null,"locator","original","a".repeat(64),"b".repeat(64),0,
            null,null,null,null,null,null,"publisher",null,"en")
        val members=mutableListOf("c");val retained=mutableListOf("c");val required=mutableListOf("c" to "d")
        val conflicts=mutableListOf(ConflictDecision(members,"RESOLVED","fixture",null,retained,required))
        val relations=mutableListOf(SourceRelation("c","d","requires","fixture",1.0))
        val derived=mutableListOf(DerivedText("c","generator","en","original","a".repeat(64),"human-reviewed","fixture","reviewer","2026-10-10"))
        val identity=PackIdentity("pack","1.0.0","c".repeat(64))
        val origins=mutableListOf(EvidenceOrigin(identity,chunk,SourceMetadata(null,null,null,null,"key",relations),derived,
            true,1,2,.75,.03,CalibrationSnapshot("UNCALIBRATED",null,null),conflicts))
        val row=CandidateDiagnostic("key",identity,"c","s",chunk.textSha256,chunk.originalSha256,true,1,2,.75,.03,true,1,origins)
        val identities=mutableListOf(identity);val manifests=mutableListOf("signed bytes")
        val context=GenerationContext(Query("question","2026-10-10"),identities,FrozenProfile(),null,manifests)
        val pool=mutableListOf(row);val captured=QueryDiagnostics(context,pool,1.0,2.0,null,false)
        members.clear();retained.clear();required.clear();conflicts.clear();relations.clear();derived.clear();origins.clear();pool.clear();identities.clear();manifests.clear()
        val owned=captured.candidates!!.single()
        assertEquals("c",owned.chunkId);assertEquals(.75,owned.cosine,0.0);assertEquals(listOf(identity),captured.context.identities)
        assertEquals(listOf("signed bytes"),captured.context.manifests)
        assertEquals("requires",owned.origins.single().metadata.relations.single().relationType)
        assertEquals("reviewer",owned.origins.single().derived.single().reviewerId)
        assertEquals(listOf("c" to "d"),owned.origins.single().conflicts.single().required)
        assertNull(owned.origins.single().calibration.agreed)
        assertThrows(UnsupportedOperationException::class.java) { (captured.candidates as MutableList).clear() }
        assertThrows(UnsupportedOperationException::class.java) { (owned.origins.single().conflicts.single().required as MutableList).clear() }
        assertThrows(UnsupportedOperationException::class.java) { (owned.origins.single().metadata.relations as MutableList).clear() }
    }
    @Test fun notReturnedAndReturnedEmptyPoolsAreDistinct() {
        val context=GenerationContext(Query("question","2026-10-10"),emptyList(),FrozenProfile(),null,emptyList())
        val missing=QueryDiagnostics(context,null,null,null,null,false)
        val empty=QueryDiagnostics(context,emptyList(),0.0,1.0,null,false)
        assertNull(missing.candidates);assertTrue(empty.candidates!!.isEmpty())
        assertNull(missing.embeddingMs);assertEquals(0.0,empty.embeddingMs!!,0.0)
        assertFalse(empty.generationCalled)
    }
}
