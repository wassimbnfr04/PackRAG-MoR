package org.packrag.product

import android.content.Context
import java.io.Closeable
import java.io.File
import org.json.JSONObject
import org.packrag.embedding.GraniteEncoder
import org.packrag.generator.LlamaGenerator
import org.packrag.generator.GeneratorBackend
import org.packrag.model.Answer
import org.packrag.model.Query
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier
import org.packrag.runtime.PackRag
import org.packrag.runtime.RuntimeTrace
import org.packrag.runtime.ConfiguredAssets
import org.packrag.runtime.SessionDiagnostics
import java.util.concurrent.atomic.AtomicLong

/** Shared actual session for the interactive product and its device integration tests. */
class ProductSession(context: Context, registryRoot: File, keys: List<ByteArray>, developerMode: Boolean) : Closeable {
    private val files = context.filesDir
    private val lock = context.assets.open("toolchain.lock.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
    private val schema = context.assets.open("schema.sql").bufferedReader(Charsets.UTF_8).use { it.readText() }
    private val configuredAssets=lock.getJSONObject("generator").let {
        require(it.getString("artifact")=="LFM2.5-2.6B-QAD-Q4_0.gguf" && it.getString("sha256")==LlamaGenerator.MODEL_SHA
            && it.getString("chat_template_sha256")==LlamaGenerator.TEMPLATE_SHA && it.getString("llama_cpp_commit")==LlamaGenerator.COMMIT)
        ConfiguredAssets(it.getString("model_id"),it.getString("artifact"),"QAD-Q4_0 (configured hash-pinned artifact)",
            lock.getJSONObject("embedder").getJSONObject("pack_profile").toString())
    }
    val registry = PackRegistry(registryRoot, PackVerifier(keys, lock.getJSONObject("embedder").getJSONObject("pack_profile"), schema, developerMode))
    private var encoder: GraniteEncoder? = null
    @Volatile private var generator: GeneratorBackend? = null
    @Volatile private var runtime: PackRag? = null
    private val cancellation = AtomicLong(0)
    val generatorLoadAndVerificationMs: Double? get() = generator?.loadAndVerificationMs
    private fun observedSession()=SessionDiagnostics(configuredAssets,encoder!=null,generator?.identity,generator?.loadAndVerificationMs)

    @Synchronized fun ask(query: Query): RuntimeTrace {
        val start = System.nanoTime()
        val ticket = cancellation.get()
        if (registry.snapshot().isEmpty()) return RuntimeTrace(Answer("NO_ACTIVE_PACK"), emptyList(), totalMs = (System.nanoTime() - start) / 1e6,session=observedSession())
        var initialization = 0.0
        if (runtime == null) {
            val hashes = lock.getJSONObject("embedder").getJSONObject("asset_sha256")
            if (encoder == null) encoder = GraniteEncoder(File(files, "models/granite"), hashes.getString("tokenizer.json"), hashes.getString("onnx/model.onnx"))
            if (generator == null) generator = LlamaGenerator(File(files, "models/LFM2.5-2.6B-QAD-Q4_0.gguf"), File(files, "models/chat_template.jinja"))
            runtime = PackRag(registry, encoder!!, generator!!)
            initialization = (System.nanoTime() - start) / 1e6
        }
        if (ticket != cancellation.get()) return RuntimeTrace(Answer("CANCELLED"), emptyList(), totalMs = (System.nanoTime() - start) / 1e6, initializationMs = initialization,session=observedSession())
        val observed=observedSession()
        return runtime!!.ask(query) { ticket != cancellation.get() }.copy(totalMs = (System.nanoTime() - start) / 1e6, initializationMs = initialization,session=observed)
    }
    fun cancel() { cancellation.incrementAndGet(); runtime?.cancel() ?: generator?.cancel() }
    @Synchronized override fun close() {
        runtime = null; generator?.close(); generator = null; encoder?.close(); encoder = null; registry.close()
    }
}
