package org.packrag.product

import android.content.pm.PackageManager
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.Locale
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.generator.LlamaGenerator
import org.packrag.model.Query
import org.packrag.runtime.RuntimeTrace

@RunWith(AndroidJUnit4::class)
class ProductE2eTest {
    @Test fun actualLocalQuestionToVerifiedCitedAnswerAndAbstention() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        assertFalse(context.packageManager.getPackageInfo(context.packageName, PackageManager.GET_PERMISSIONS).requestedPermissions?.contains("android.permission.INTERNET") ?: false)
        val assets = instrumentation.context.assets
        val key = assets.open("developer-public-key.raw").use { it.readBytes() }
        val fixtures = assets.open("e2e-cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val directory = File(context.filesDir, "m2-e2e-${UUID.randomUUID()}"); assertTrue(directory.mkdirs())
        val archive = File(directory, "input.kpack")
        assets.open("walking-skeleton.kpack").use { input -> archive.outputStream().use { input.copyTo(it) } }
        val results = JSONArray()
        val progress = File(context.filesDir, "m2-e2e-progress.json")
        var status = "RUNNING"
        fun save() { progress.writeText(JSONObject().put("status", status).put("cases", results).toString(2), Charsets.UTF_8) }
        fun record(id: String, trace: RuntimeTrace, passed: Boolean) {
            val item = JSONObject().put("id", id).put("passed", passed).put("state", trace.answer.state)
                .put("answer", trace.answer.text ?: JSONObject.NULL).put("selected", JSONArray(trace.selected))
                .put("prefill_tokens", trace.prefillTokens).put("evidence_tokens", trace.evidenceTokens)
                .put("actual_emitted_tokens_including_terminal", trace.emittedTokens)
                .put("reasoning_tokens", trace.reasoningTokens ?: JSONObject.NULL)
                .put("final_and_terminal_tokens", trace.finalAndTerminalTokens ?: JSONObject.NULL)
                .put("prefill_ms", trace.prefillMs ?: JSONObject.NULL).put("decode_wall_ms", trace.decodeWallMs ?: JSONObject.NULL)
                .put("first_model_token_ms_including_hidden_reasoning", trace.firstEmittedTokenMs ?: JSONObject.NULL)
                .put("question_wall_ms_including_lazy_initialization", trace.totalMs)
                .put("lazy_initialization_ms", trace.initializationMs)
                .put("sources", JSONArray(trace.answer.sources.map { source -> JSONObject().put("id", source.evidenceId)
                    .put("canonical_text", source.canonicalText).put("title", source.title).put("locator", source.locator)
                    .put("publisher", source.publisher).put("pack_id", source.pack.packId).put("version", source.pack.version)
                    .put("manifest_sha256", source.pack.manifestSha256) }))
            results.put(item); save(); assertTrue("Actual phone E2E failed: $id state=${trace.answer.state}", passed)
        }
        save()
        try {
            ProductSession(context, File(directory, "registry"), listOf(key), developerMode = true).use { session ->
                val absent = session.ask(Query("Aster-9 temperature limit?", "2026-10-05"))
                record("M2-NO-PACK", absent, absent.answer.state == "NO_ACTIVE_PACK")
                assertNull(session.generatorLoadAndVerificationMs)
                session.registry.activate(archive)
                val cases = fixtures.getJSONArray("supported")
                var first: RuntimeTrace? = null
                for (index in 0 until cases.length()) {
                    val case = cases.getJSONObject(index)
                    val trace = session.ask(Query(case.getString("question"), "2026-10-05"))
                    if (index == 0) first = trace
                    val passed = trace.answer.state == "ANSWER_ACCEPTED" &&
                        (trace.answer.text ?: "").lowercase(Locale.ROOT).contains(case.getString("smoke_expected_fact").lowercase(Locale.ROOT)) &&
                        trace.answer.sources.isNotEmpty() && trace.answer.text?.contains("</think>") != true
                    record("M2-${case.getString("case_id")}", trace, passed)
                }
                val unrelated = session.ask(Query("Who won the most recent football championship?", "2026-10-05"))
                record("M2-UNRELATED", unrelated, unrelated.answer.state == "NO_RELEVANT_EVIDENCE" && unrelated.emittedTokens == 0)
                val insufficient = session.ask(Query("What is the Aster-9 controller purchase price?", "2026-10-05"))
                record("M2-EXACT-NOT-SUFFICIENT", insufficient, insufficient.answer.state == "INSUFFICIENT_EVIDENCE" && insufficient.answer.text == null)
                val repeated = session.ask(Query(cases.getJSONObject(0).getString("question"), "2026-10-05"))
                record("M2-REPEATED-CONTEXT-RESET", repeated, repeated.answer.state == first!!.answer.state && repeated.answer.text == first!!.answer.text)
                status = "PASS"; save()
                File(context.filesDir, "m2-product-e2e.json").writeText(JSONObject().put("status", status).put("cases", results)
                    .put("purpose", "M2_REAL_DEVELOPMENT_ANDROID_E2E_NOT_RELEASE_OR_PACKBENCH")
                    .put("model_sha256", LlamaGenerator.MODEL_SHA).put("template_sha256", LlamaGenerator.TEMPLATE_SHA)
                    .put("llama_cpp_commit", LlamaGenerator.COMMIT).put("cpu_threads", 4).put("context", 2048)
                    .put("load_hash_and_context_ms", session.generatorLoadAndVerificationMs)
                    .put("raw_reasoning_persisted", false).put("network_mode", "MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET")
                    .put("limits", "Synthetic exact-alias admission; automatically checked smoke facts/structural citations; not semantic human review, calibrated packs or peak memory/interactive thermal acceptance")
                    .toString(2), Charsets.UTF_8)
            }
        } catch (failure: Throwable) { status = "FAIL"; save(); throw failure }
        finally { require(directory.canonicalPath.startsWith(context.filesDir.canonicalPath + File.separator)); directory.deleteRecursively() }
    }
}
