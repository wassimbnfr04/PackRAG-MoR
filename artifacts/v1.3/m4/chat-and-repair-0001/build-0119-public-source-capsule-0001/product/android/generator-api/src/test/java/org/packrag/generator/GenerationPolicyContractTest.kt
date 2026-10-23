package org.packrag.generator

import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class GenerationPolicyContractTest {
    private fun quotes()=GenerationPolicy.quotes(File(System.getProperty("packrag.repo"),"product/config/generation-profile-quotes-v1.json").readBytes())
    @Test fun hashApprovedPolicyAndBaselineRemainIndependent() {
        val bytes=File(System.getProperty("packrag.repo"),"product/config/generation-profile-quotes-v1.json").readBytes()
        val policy=GenerationPolicy.quotes(bytes);bytes[0]=0
        assertEquals(3072,policy.context);assertEquals(1536,policy.generated)
        assertEquals(GenerationPolicy.QUOTE_CONFIG_SHA,policy.configSha256)
        assertEquals(2048,GenerationPolicy.BASELINE.context);assertEquals(512,GenerationPolicy.BASELINE.generated)
        assertEquals("BASE",GenerationPolicy.BASELINE.system("BASE"))
        assertThrows(IllegalArgumentException::class.java){GenerationPolicy.quotes(bytes)}
    }
    @Test fun requestOwnsTokensUnitsAndContextBudget() {
        val tokens=intArrayOf(7,8);val texts=mutableListOf("PRIVATE_SOURCE_TEST_TEXT")
        val request=GenerationRequest(quotes(),tokens,1536,texts)
        tokens[0]=99;texts.clear();request.tokens[1]=99
        assertArrayEquals(intArrayOf(7,8),request.tokens)
        assertEquals(listOf("PRIVATE_SOURCE_TEST_TEXT [S1]"),request.units)
        assertFalse(request.toString().contains("PRIVATE_SOURCE"))
        assertThrows(UnsupportedOperationException::class.java){(request.units as MutableList).clear()}
        assertThrows(IllegalArgumentException::class.java){GenerationRequest(GenerationPolicy.BASELINE,intArrayOf(1),513,emptyList())}
        assertThrows(IllegalArgumentException::class.java){GenerationRequest(quotes(),IntArray(1537),1,listOf("x"))}
    }
    @Test fun unicodeUnitAndGrammarBytesMatchIndependentPythonFixture() {
        val row=JSONObject(requireNotNull(javaClass.getResource("/quote-protocol-parity-v1.json")).readText())
        fun strings(key:String)=row.getJSONArray(key).let{a->(0 until a.length()).map{a.getString(it)}}
        val units=QuoteProtocol.units(strings("texts"));assertEquals(strings("units"),units)
        assertArrayEquals(row.getString("grammar").toByteArray(Charsets.UTF_8),QuoteProtocol.grammar(units).toByteArray(Charsets.UTF_8))
    }
    @Test fun admissionRejectsInventedCitedTextWrongIdentityOrderingAndDuplicates() {
        val units=QuoteProtocol.units(listOf("Disconnect power.","Débrancher l’alimentation."))
        assertTrue(QuoteProtocol.matches("1. Disconnect power. [S1]\n2. Débrancher l’alimentation. [S2]",units))
        for(value in listOf("1. Connect power. [S1]","1. Disconnect power. [S9]","2. Disconnect power. [S1]",
            "1. Disconnect power. [S1]\n2. Disconnect power. [S1]"))assertFalse(QuoteProtocol.matches(value,units))
        assertThrows(IllegalArgumentException::class.java){QuoteProtocol.units(listOf("\n\n"))}
        assertThrows(IllegalArgumentException::class.java){QuoteProtocol.units(List(5){"x"})}
        assertThrows(IllegalArgumentException::class.java){QuoteProtocol.units(listOf((0..64).joinToString("\n")))}
    }
}
