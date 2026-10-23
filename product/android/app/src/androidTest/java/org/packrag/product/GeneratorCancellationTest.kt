package org.packrag.product

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.generator.LlamaGenerator
import org.packrag.generator.GeneratorBackend
import org.packrag.generator.GenerationResult
import org.packrag.runtime.OutputValidator

@RunWith(AndroidJUnit4::class)
class GeneratorCancellationTest {
    @Test fun actualNativeAbortRecoveryAndClosedHandleRejection() {
        val instrument = InstrumentationRegistry.getInstrumentation()
        val context = instrument.targetContext
        val reference = instrument.context.assets.open("parity-reference.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val case = reference.getJSONArray("prompt_cases").getJSONObject(0)
        val tokens = case.getJSONArray("tokens")
        val prompt = IntArray(tokens.length()) { tokens.getInt(it) }
        val models = File(context.filesDir, "models")
        val generator: GeneratorBackend = LlamaGenerator(File(models, "LFM2.5-2.6B-QAD-Q4_0.gguf"), File(models, "chat_template.jinja"))
        assertEquals(LlamaGenerator.MODEL_SHA,generator.identity.modelSha256)
        assertEquals(LlamaGenerator.TEMPLATE_SHA,generator.identity.templateSha256)
        assertEquals(LlamaGenerator.COMMIT,generator.identity.runtimeRevision)
        val executor = Executors.newSingleThreadExecutor()
        try {
            val future = executor.submit<GenerationResult> { generator.generate(prompt, 512) }
            val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(10)
            while (!generator.isGenerating && !future.isDone && System.nanoTime() < deadline) Thread.sleep(5)
            assertTrue("Native generation did not begin", generator.isGenerating)
            Thread.sleep(20)
            val started = System.nanoTime(); generator.cancel()
            val cancelled = future.get(30, TimeUnit.SECONDS)
            val latency = (System.nanoTime() - started) / 1e6
            assertEquals(2, cancelled.stop); cancelled.buffer.fill(0)
            val recovery = generator.generate(prompt, case.getInt("max_new"))
            val final = try { OutputValidator.validate(recovery.buffer.toString(Charsets.UTF_8), setOf("S1", "S2", "S3", "S4"), recovery.stop == 1) }
                finally { recovery.buffer.fill(0) }
            assertEquals("ANSWER_ACCEPTED", final.state); assertTrue(final.text!!.contains("74"))
            generator.close()
            assertThrows(IllegalStateException::class.java) { generator.tokenize("closed") }
            generator.cancel(); generator.close() // Idempotent cancellation/close after teardown.
            File(context.filesDir, "m2-generator-cancellation.json").writeText(JSONObject().put("status", "PASS")
                .put("native_cancel_stop", cancelled.stop).put("cancel_return_ms", latency)
                .put("post_cancel_recovery_state", final.state).put("post_cancel_final_answer", final.text)
                .put("closed_handle_rejected", true).put("idempotent_close_cancel", true)
                .put("consumer_contract","GeneratorBackend/GenerationResult")
                .put("backend",generator.identity.backend).put("model_sha256",generator.identity.modelSha256)
                .put("template_sha256",generator.identity.templateSha256).put("runtime_revision",generator.identity.runtimeRevision)
                .put("purpose", "NATIVE_CANCEL_LIFECYCLE_NOT_LATENCY_ACCEPTANCE").toString(2), Charsets.UTF_8)
        } finally { generator.cancel(); executor.shutdownNow(); generator.close() }
    }
}
