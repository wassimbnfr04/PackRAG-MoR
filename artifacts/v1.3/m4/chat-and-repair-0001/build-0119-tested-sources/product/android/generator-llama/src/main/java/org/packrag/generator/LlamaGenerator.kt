package org.packrag.generator

import java.io.File
import java.util.concurrent.atomic.AtomicLong
import org.packrag.crypto.RawManifestVerifier as Crypto

internal object LlamaNative {
    init { System.loadLibrary("packrag_jni") }
    external fun abi():ByteArray
    external fun load(file: ByteArray, vocabularyOnly: Boolean, threads: Int,contextTokens:Int): Long
    external fun tokenize(handle: Long, text: ByteArray, addSpecial: Boolean): IntArray
    external fun begin(handle: Long)
    external fun generate(handle: Long, prompt: IntArray, maximum: Int,grammar:ByteArray?,mode:Int): NativeEmission
    external fun cancel(handle: Long)
    external fun close(handle: Long)
}

/** Raw buffer stays in memory. Its toString never reveals reasoning. */
class NativeEmission(override val buffer: ByteArray, override val emitted: IntArray, override val stop: Int,
    override val prefillMs: Double, override val decodeWallMs: Double, override val firstEmittedTokenMs: Double, override val totalMs: Double) : GenerationResult {
    override fun toString(): String = "NativeEmission(stop=$stop, emitted=${emitted.size})"
}

class LlamaGenerator(model: File, template: File, vocabularyOnly: Boolean = false, threads: Int = 4,
    override val generationPolicy:GenerationPolicy=GenerationPolicy.BASELINE) : GeneratorBackend {
    private val initializationStarted=System.nanoTime()
    private val handle: AtomicLong
    @Volatile override var isGenerating: Boolean = false
        private set
    override val loadAndVerificationMs: Double
    val nativeAbi=LlamaNative.abi().toString(Charsets.UTF_8)
    override val identity = GeneratorIdentity(MODEL_SHA,TEMPLATE_SHA,COMMIT,"lfm25-llama-cpu-android-$nativeAbi",nativeSha(nativeAbi))
    init {
        val start = initializationStarted
        require(Crypto.fileHash(model) == MODEL_SHA) { "Generator model hash mismatch" }
        require(Crypto.fileHash(template) == TEMPLATE_SHA) { "Generator template hash mismatch" }
        handle = AtomicLong(LlamaNative.load(model.absolutePath.toByteArray(Charsets.UTF_8), vocabularyOnly, threads,generationPolicy.context))
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
    override fun generate(tokens: IntArray, maximum: Int, cancelled: () -> Boolean): NativeEmission {
        check(!generationPolicy.quoted){"QUOTATION_REQUIRES_OWNED_EVIDENCE"}
        return generate(GenerationRequest(generationPolicy,tokens,maximum,emptyList()),cancelled)
    }
    @Synchronized override fun generate(request:GenerationRequest,cancelled:()->Boolean):NativeEmission {
        check(request.policy.profileId==generationPolicy.profileId && request.policy.configSha256==generationPolicy.configSha256){"GENERATION_POLICY_CHANGED"}
        val current = handle.get(); check(current != 0L)
        LlamaNative.begin(current)
        isGenerating = true
        try {
            // A cancellation during admission must survive the native per-query reset.
            if (cancelled()) LlamaNative.cancel(current)
            return LlamaNative.generate(current, request.tokens, request.maximum,request.grammar?.toByteArray(Charsets.UTF_8),if(generationPolicy.quoted)1 else 0)
        } finally { isGenerating = false }
    }
    override fun cancel() { LlamaNative.cancel(handle.get()) }
    override fun close() { LlamaNative.close(handle.getAndSet(0)) }
    companion object {
        // Acceptance inspects actual APK library bytes against this pin.
        // This field is not an in-process library hash measurement.
        const val NATIVE_SHA = "5cf4b9131b3532f65d4fcfe88a7dfd172183518f738f971ee7d8321e6f5682a7"
        const val X86_NATIVE_SHA = "e7cf27062fc074bb3cef513593e9d4d213c8dc3e6432344a3c18a73058105715"
        fun nativeSha(abi:String)=when(abi){"arm64-v8a"->NATIVE_SHA;"x86_64"->X86_NATIVE_SHA;else->error("Unsupported generator ABI")}
        const val MODEL_SHA = "a247afd6414918eac8e520a9e6137dc271235461ecbe1180462221d5b8d40b03"
        const val TEMPLATE_SHA = "ea663864491de7ade391839479860ca95541f892f72665c73251fbd4643b1bef"
        const val COMMIT = "19e28a27702117d8f2eb16b825b9a308111f67d9"
    }
}
