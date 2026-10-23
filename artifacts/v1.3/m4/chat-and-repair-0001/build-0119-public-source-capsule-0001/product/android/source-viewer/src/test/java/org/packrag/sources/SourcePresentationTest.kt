package org.packrag.sources

import org.junit.Assert.*
import org.junit.Test
import org.packrag.model.*

class SourcePresentationTest {
    @Test fun exactSignedAssertionsRemainDistinctFromUnknownValues() {
        val attribution=SourceAttribution(null,"2026-10-10","  CC0-1.0  ",false,"synthetic",null,"\nexact notes\n")
        val lines=attributionLines(attribution).associate { it.label to it.value }
        assertEquals("Unknown",lines["Canonical URI"]);assertEquals("false",lines["Declared redistribution allowed"])
        assertEquals("  CC0-1.0  ",lines["Declared license"]);assertEquals("\nexact notes\n",lines["Source notes"])
        assertEquals("Unknown",attributionLines(null).single { it.label=="Declared redistribution allowed" }.value)
        assertEquals("No packaged original snapshot",lines["Packaged snapshot path"])
    }
    @Test fun inheritedUnknownAndExclusiveIntersectionAreNotConfused() {
        val chunk=Chunk("chunk","source","Title","Source title",null,"Article-1","نص أصلي","0".repeat(64),"1".repeat(64),0,
            "MA",null,"2027-01-01","2026-01-01",null,"historical","Publisher",null,"ar")
        val lines=validityLines(validityProvenance(chunk)).associate { it.label to it.value }
        assertEquals("Unknown",lines["Source start"]);assertEquals("2026-01-01",lines["Effective intersection start"])
        assertEquals("Inherits source end (2027-01-01)",lines["Chunk end (exclusive)"]);assertEquals("2027-01-01",lines["Effective intersection end (exclusive)"])
        val source=SourceRecord("S1",chunk.canonicalText,chunk.sourceTitle,chunk.locator,chunk.publisher,PackIdentity("org.packrag.test","1.0.0","a".repeat(64)),
            validity=validityProvenance(chunk),canonicalLanguage="ar",canonicalTextSha256=chunk.textSha256,originalSha256=chunk.originalSha256,chunkId=chunk.id,sourceId=chunk.sourceId)
        assertEquals("نص أصلي",source.canonicalText);assertEquals("ar",sourceLines(source).single { it.label=="Canonical language" }.value)
        assertEquals("Unknown",sourceLines(source).single { it.label=="Signing key" }.value)
    }
    @Test fun packDetailsCopyTheirCollectionsAndKeepOrphanSources() {
        val source=PackSourceDetails("unused","Sans fragment","Publisher","fr","b".repeat(64),SourceAttribution(null,"2026-10-10","CC0-1.0",false,"synthetic",null),null,null,null,null,null,null,null)
        val sources=mutableListOf(source);val languages=mutableListOf("en","fr");val jurisdictions=mutableListOf("MA")
        val details=PackDetails(PackIdentity("org.packrag.test","1.0.0","a".repeat(64)),"Pack","repair","Publisher","key","2026-10-10T00:00:00Z","2027-01-01",
            languages,jurisdictions,"{}","{}","{}","UNCALIBRATED",100,200,300,0,sources)
        sources.clear();languages.clear();jurisdictions.clear()
        assertEquals(listOf(source),details.sources);assertEquals(listOf("en","fr"),details.languages);assertEquals(listOf("MA"),details.jurisdictions)
        assertEquals(0,details.chunkCount);assertThrows(UnsupportedOperationException::class.java) { (details.sources as MutableList).clear() }
    }
}
