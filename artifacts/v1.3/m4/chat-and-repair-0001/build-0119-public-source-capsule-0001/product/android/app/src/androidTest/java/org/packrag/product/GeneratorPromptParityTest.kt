package org.packrag.product

import android.content.pm.PackageManager
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.embedding.GraniteEncoder
import org.packrag.generator.LlamaGenerator
import org.packrag.model.Query
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier
import org.packrag.retrieval.Retrieval
import org.packrag.runtime.Prompt

@RunWith(AndroidJUnit4::class)
class GeneratorPromptParityTest {
    @Test fun actualGgufTokenizerAndBudgetedOfficialPromptParity() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        assertFalse(context.packageManager.getPackageInfo(context.packageName, PackageManager.GET_PERMISSIONS).requestedPermissions?.contains("android.permission.INTERNET") ?: false)
        val assets = instrumentation.context.assets
        val reference = assets.open("parity-reference.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val xmlReference=assets.open("prompt-v13-xml-corpus/prompt-reference.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        assertEquals("V1.3_XML_ENVELOPE",xmlReference.getString("prompt_serialization"))
        val embedder = reference.getJSONObject("lock").getJSONObject("embedder")
        val key = assets.open("developer-public-key.raw").use { it.readBytes() }
        val schema = assets.open("schema.sql").bufferedReader(Charsets.UTF_8).use { it.readText() }
        val owned = File(context.filesDir, "m2-generator-token-parity-${UUID.randomUUID()}")
        assertTrue(owned.mkdirs())
        val archive = File(owned, "input.kpack")
        assets.open("walking-skeleton.kpack").use { source -> archive.outputStream().use { source.copyTo(it) } }
        val results = JSONArray()
        val models = File(context.filesDir, "models")
        LlamaGenerator(File(models, "LFM2.5-2.6B-QAD-Q4_0.gguf"), File(models, "chat_template.jinja"), vocabularyOnly = true).use { generator ->
            PackRegistry(File(owned, "registry"), PackVerifier(listOf(key), embedder.getJSONObject("pack_profile"), schema, true)).use { registry ->
                registry.activate(archive)
                val hashes = embedder.getJSONObject("asset_sha256")
                GraniteEncoder(File(models, "granite"), hashes.getString("tokenizer.json"), hashes.getString("onnx/model.onnx")).use { encoder ->
                    val cases = xmlReference.getJSONArray("prompt_cases")
                    for (index in 0 until cases.length()) {
                        val case = cases.getJSONObject(index)
                        val query = Query(case.getString("query"), case.getString("as_of"))
                        assertEquals(case.getString("normalized_embedding_input"),query.normalized)
                        val retrieved = Retrieval.retrieve(registry.snapshot(), query, encoder.encode(query.normalized))
                        val prepared = Prompt.prepare(query, registry.snapshot(), retrieved.candidates, generator)
                        assertEquals(case.getString("system"), Prompt.SYSTEM)
                        assertEquals(case.getString("user"), Prompt.user(query, registry.snapshot(), prepared.evidence))
                        val ids = case.getJSONArray("tokens")
                        assertArrayEquals(case.getString("id"), IntArray(ids.length()) { ids.getInt(it) }, prepared.tokens)
                        assertEquals(case.getInt("evidence_tokens"), prepared.evidenceTokens)
                        assertEquals(case.getInt("prefill"), prepared.tokens.size)
                        assertEquals(case.getInt("max_new"), prepared.maximum)
                        val selected = case.getJSONArray("selected")
                        assertEquals(List(selected.length()) { selected.getString(it) }, prepared.evidence.map { it.chunk.id })
                        results.put(JSONObject().put("id", case.getString("id")).put("status", "PASS").put("prefill_tokens", prepared.tokens.size)
                            .put("evidence_tokens", prepared.evidenceTokens).put("selected_chunks", JSONArray(prepared.evidence.map { it.chunk.id })))
                    }
                }
            }
            File(context.filesDir, "m2-generator-prompt-parity.json").writeText(JSONObject().put("status", "PASS")
                .put("prompt_serialization","V1.3_XML_ENVELOPE").put("normalized_query_embedding",true)
                .put("purpose", "GGUF_VOCABULARY_ONLY_PROMPT_PARITY_NOT_WEIGHT_INFERENCE").put("cases", results)
                .put("model_sha256", LlamaGenerator.MODEL_SHA).put("template_sha256", LlamaGenerator.TEMPLATE_SHA)
                .put("llama_cpp_commit", LlamaGenerator.COMMIT).put("load_hash_and_vocabulary_ms", generator.loadAndVerificationMs).toString(2), Charsets.UTF_8)
        }
        require(owned.canonicalPath.startsWith(context.filesDir.canonicalPath + File.separator)); owned.deleteRecursively()
    }
}
