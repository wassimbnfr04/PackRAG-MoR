package org.packrag.generator

import java.io.File
import java.util.concurrent.atomic.AtomicLong
import org.packrag.crypto.RawManifestVerifier as Crypto

internal object LlamaNative {
    init { System.loadLibrary("packrag_jni") }
    external fun load(file: ByteArray, vocabularyOnly: Boolean, threads: Int): Long
    external fun tokenize(handle: Long, text: ByteArray, addSpecial: Boolean): IntArray
    external fun begin(handle: Long)
    external fun generate(handle: Long, prompt: IntArray, maximum: Int): NativeEmission
    external fun cancel(handle: Long)
    external fun close(handle: Long)
}

/** Raw buffer stays in memory. Its toString never reveals reasoning. */
class NativeEmission(override val buffer: ByteArray, override val emitted: IntArray, override val stop: Int,
    override val prefillMs: Double, override val decodeWallMs: Double, override val firstEmittedTokenMs: Double, override val totalMs: Double) : GenerationResult {
    override fun toString(): String = "NativeEmission(stop=$stop, emitted=${emitted.size})"
}

class LlamaGenerator(model: File, template: File, vocabularyOnly: Boolean = false, threads: Int = 4) : GeneratorBackend {
    private val handle: AtomicLong
    @Volatile override var isGenerating: Boolean = false
        private set
    override val loadAndVerificationMs: Double
    override val identity = GeneratorIdentity(MODEL_SHA,TEMPLATE_SHA,COMMIT,"lfm25-llama-cpu-android",NATIVE_SHA)
    init {
        val start = System.nanoTime()
        require(Crypto.fileHash(model) == MODEL_SHA) { "Generator model hash mismatch" }
        require(Crypto.fileHash(template) == TEMPLATE_SHA) { "Generator template hash mismatch" }
        handle = AtomicLong(LlamaNative.load(model.absolutePath.toByteArray(Charsets.UTF_8), vocabularyOnly, threads))
        require(handle.get() != 0L)
        loadAndVerificationMs = (System.nanoTime() - start) / 1e6
    }
    override fun tokenize(text: String, addSpecial: Boolean): IntArray = LlamaNative.tokenize(handle.get(), text.toByteArray(Charsets.UTF_8), addSpecial)
    override fun renderTokens(system: String, user: String): IntArray {
        // Exact audited official one-turn template; full actual IDs are gated against Jinja references.
        val body = "<|im_start|>system\n$system<|im_end|>\n<|im_start|>user\n$user<|im_end|>\n<|im_start|>assistant\n<think>"
        val explicit = tokenize("<|startoftext|>$body")
        require(explicit.contentEquals(tokenize(body, true))) { "Generator BOS parity mismatch" }
        return explicit
    }
    @Synchronized override fun generate(tokens: IntArray, maximum: Int, cancelled: () -> Boolean): NativeEmission {
        val current = handle.get(); check(current != 0L)
        LlamaNative.begin(current)
        isGenerating = true
        try {
            // A cancellation during admission must survive the native per-query reset.
            if (cancelled()) LlamaNative.cancel(current)
            return LlamaNative.generate(current, tokens, maximum)
        } finally { isGenerating = false }
    }
    override fun cancel() { LlamaNative.cancel(handle.get()) }
    override fun close() { LlamaNative.close(handle.getAndSet(0)) }
    companion object {
        // Acceptance inspects actual APK library bytes against this pin.
        // This field is not an in-process library hash measurement.
        const val NATIVE_SHA = "361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef"
        const val MODEL_SHA = "a247afd6414918eac8e520a9e6137dc271235461ecbe1180462221d5b8d40b03"
        const val TEMPLATE_SHA = "ea663864491de7ade391839479860ca95541f892f72665c73251fbd4643b1bef"
        const val COMMIT = "19e28a27702117d8f2eb16b825b9a308111f67d9"
    }
}
