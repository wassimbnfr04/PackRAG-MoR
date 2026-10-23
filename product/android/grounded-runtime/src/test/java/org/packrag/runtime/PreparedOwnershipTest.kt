package org.packrag.runtime

import org.junit.Assert.*
import org.junit.Test
import org.packrag.model.Query
import org.packrag.model.PackIdentity
import org.packrag.model.SelectionPlan
import org.packrag.model.SelectionDecision

class PreparedOwnershipTest {
    @Test fun preparedTokensAndSelectionDecisionsHaveDefensiveOwnership() {
        val tokens=intArrayOf(7,8)
        val keys=mutableListOf("a");val trial=mutableListOf("a");val sources=mutableListOf("s")
        val decisions=mutableListOf(SelectionDecision("a","SELECTED",trial))
        val context=GenerationContext(Query("question","2026-10-09"),emptyList(),FrozenProfile(),null,emptyList())
        val prepared=PreparedPrompt(tokens,emptyList(),100,512,emptyList(),SelectionPlan(keys,decisions,sources),context)
        tokens[0]=99;keys.clear();trial.clear();sources.clear();decisions.clear()
        val exposed=prepared.tokens;exposed[1]=99
        assertArrayEquals(intArrayOf(7,8),prepared.tokens)
        assertEquals(listOf("a"),prepared.selection.keys)
        assertEquals(listOf("a"),prepared.selection.decisions.single().trial)
        assertEquals(listOf("s"),prepared.selection.sources)
        assertThrows(UnsupportedOperationException::class.java) { (prepared.selection.decisions.single().trial as MutableList).clear() }
    }
    @Test fun activeQueryProfileAndManifestContextOwnCallerCollections() {
        val identities=mutableListOf(PackIdentity("pack","1.0.0","a".repeat(64)));val manifests=mutableListOf("original")
        val context=GenerationContext(Query("Raw <question>","2026-10-09","MA",true),identities,FrozenProfile(),null,manifests)
        identities.clear();manifests.clear()
        assertEquals("pack",context.identities.single().packId);assertEquals("original",context.manifests.single())
        assertEquals("Raw <question>",context.query.raw);assertEquals("raw <question>",context.query.normalized)
        assertEquals(2048,context.profile.context);assertEquals(1536,context.profile.prefill)
        assertEquals(1200,context.profile.evidence);assertEquals(4,context.profile.chunks);assertEquals(512,context.profile.generated)
        assertThrows(UnsupportedOperationException::class.java) { (context.identities as MutableList).clear() }
    }
}
