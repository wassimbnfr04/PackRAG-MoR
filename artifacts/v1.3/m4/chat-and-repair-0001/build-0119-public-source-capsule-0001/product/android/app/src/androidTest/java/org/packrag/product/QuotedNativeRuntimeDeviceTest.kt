package org.packrag.product

import android.os.Debug
import androidx.test.ext.junit.runners.AndroidJUnit4
import java.io.File
import java.util.UUID
import java.nio.file.Files
import java.util.Comparator
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.generator.GenerationPolicy
import org.packrag.generator.GenerationRequest
import org.packrag.generator.LlamaGenerator
import org.packrag.model.Query
import org.packrag.runtime.OutputValidator
import org.packrag.runtime.Prompt

/** Actual native model; isolated registry, no Activity and no physical performance claim. */
@RunWith(AndroidJUnit4::class)
class QuotedNativeRuntimeDeviceTest {
    @Test fun actualNativePolicyParityCapCancellationAndRepairWalkingPath() {
        val context=ProductUiTestSupport.context
        val before=ChatRepairOwner.snapshot();assertTrue(before.size in listOf(5,51))
        val policy=GenerationPolicy.quotes(context.assets.open("generation-profile-quotes-v1.json").use{it.readBytes()})
        val expected=ProductUiTestSupport.instrument.context.assets.open("repair-quotation/parity.json").bufferedReader().use{JSONObject(it.readText())}
        assertEquals(policy.configSha256,expected.getString("config_sha256"))
        assertEquals(policy.system(Prompt.SYSTEM),expected.getString("system"))
        val models=File(context.filesDir,"models")
        val report=JSONObject().put("environment",if(before.size==5)"OWNED_EMULATOR_NATIVE_X86_64" else "PHYSICAL_ARM64")
            .put("owner_sha256_before",JSONObject(before)).put("raw_reasoning_persisted",false)
            .put("scope","Actual selected-evidence native functionality; sampled PSS is not peak or controlled phone performance")
        val model=File(models,"LFM2.5-2.6B-QAD-Q4_0.gguf");val template=File(models,"chat_template.jinja")
        LlamaGenerator(model,template,generationPolicy=policy).use { generator ->
            assertEquals(if(before.size==5)"x86_64" else "arm64-v8a",generator.nativeAbi)
            val tokens=generator.renderTokens(expected.getString("system"),expected.getString("user"))
            val declared=expected.getJSONArray("tokens").let{a->IntArray(a.length()){a.getInt(it)}}
            assertArrayEquals(declared,tokens)
            assertEquals(expected.getInt("closing_token"),generator.tokenize("</think>").single())
            val unitRows=expected.getJSONArray("units").let{a->(0 until a.length()).map{a.getString(it)}}
            val captured=unitRows.map { unit ->
                val match=requireNotNull(Regex("(.*) \\[S([1-4])\\]$").matchEntire(unit))
                match.groupValues[2].toInt() to match.groupValues[1]
            }.groupBy({it.first},{it.second})
            assertEquals((1..captured.size).toList(),captured.keys.toList())
            val texts=captured.toSortedMap().values.map{it.joinToString("\n")}
            val request=GenerationRequest(policy,tokens,2,texts)
            assertEquals(expected.getString("grammar"),request.grammar)
            val limited=generator.generate(request){false}
            try {
                assertEquals(1,limited.stop);assertEquals(2,limited.emitted.size)
                val rejected=OutputValidator.validate(limited.buffer.toString(Charsets.UTF_8),setOf("S1"),true,request.units)
                assertEquals("GENERATION_UNUSABLE",rejected.state);assertNull(rejected.text)
            } finally {limited.buffer.fill(0)}
            val cancelled=generator.generate(GenerationRequest(policy,tokens,1536,texts)){true}
            try {assertEquals(2,cancelled.stop);assertEquals(0,cancelled.emitted.size)}finally{cancelled.buffer.fill(0)}
            report.put("native_abi",generator.nativeAbi).put("configured_native_library_sha256",generator.identity.runtimeBinarySha256)
                .put("actual_token_template_grammar_parity",true).put("real_cap_two_rejected",true).put("real_pre_cancel_no_emission",true)
                .put("sampled_pss_after_direct_contract_kib",Debug.getPss())
        }
        val root=File(context.filesDir,"m4-native-quote-${UUID.randomUUID()}");assertFalse(root.exists());assertTrue(root.mkdir())
        val observations=JSONArray()
        try {
            ProductSession(context,File(root,"registry"),ProductConfiguration.keys(context),true,generationPolicy=policy).use { session ->
                val question=expected.getString("question");val date=expected.getString("as_of")
                assertEquals("NO_ACTIVE_PACK",session.ask(Query(question,date)).answer.state)
                session.registry.activate(File(context.filesDir,"m4-repair-fixture-0001.kpack"))
                val accepted=session.ask(Query(question,date))
                assertEquals("ANSWER_ACCEPTED",accepted.answer.state);assertEquals(1,accepted.answer.sources.size)
                val source=accepted.answer.sources.single()
                assertEquals("1. ${source.generatorRepresentation!!.text} [S1]",accepted.answer.text)
                assertEquals(3072,accepted.evidenceContext!!.profile.context);assertEquals(1536,accepted.evidenceContext!!.profile.generated)
                assertEquals(policy.configSha256,accepted.evidenceContext!!.profile.generationPolicySha256)
                assertTrue(accepted.emittedTokens in 1..1536);assertNotNull(accepted.reasoningTokens)
                observations.put(JSONObject().put("id","FAN_FULL_GUIDE").put("state",accepted.answer.state).put("final_text",accepted.answer.text)
                    .put("canonical_sha256",source.canonicalTextSha256).put("prefill_tokens",accepted.prefillTokens).put("evidence_tokens",accepted.evidenceTokens)
                    .put("emitted_tokens",accepted.emittedTokens).put("reasoning_tokens",accepted.reasoningTokens).put("total_functional_ms",accepted.totalMs))
                val missing=session.ask(Query("What exact PSI should I inflate this bicycle inner tube to?",date))
                assertEquals("INSUFFICIENT_EVIDENCE",missing.answer.state);assertNull(missing.answer.text);assertTrue(missing.answer.sources.isEmpty())
                observations.put(JSONObject().put("id","TUBE_UNDOCUMENTED_PRESSURE").put("state",missing.answer.state).put("emitted_tokens",missing.emittedTokens))
                session.registry.deactivate(session.registry.snapshot().single().id)
                assertEquals("NO_ACTIVE_PACK",session.ask(Query(question,date)).answer.state)
                report.put("sampled_pss_after_walk_kib",Debug.getPss())
            }
        } finally {
            val target=root.toPath().toAbsolutePath().normalize()
            assertEquals(context.filesDir.toPath().toAbsolutePath().normalize(),target.parent)
            assertTrue(target.fileName.toString().startsWith("m4-native-quote-"));assertFalse(Files.isSymbolicLink(target))
            Files.walk(target).use{paths->paths.sorted(Comparator.reverseOrder()).forEach{Files.delete(it)}}
            assertFalse(root.exists())
        }
        assertEquals(before,ChatRepairOwner.snapshot())
        report.put("status","PASS").put("observations",observations).put("owner_sha256_after",JSONObject(before))
        File(context.filesDir,"m4-native-quoted-runtime-0001.json").writeText(report.toString(2),Charsets.UTF_8)
    }
}
