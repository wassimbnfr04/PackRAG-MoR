package org.packrag.generator

import java.io.Closeable

data class GeneratorIdentity(val modelSha256: String, val templateSha256: String,
    val runtimeRevision: String, val backend: String,val runtimeBinarySha256:String?=null) {
    init {
        require(Regex("[0-9a-f]{64}").matches(modelSha256))
        require(Regex("[0-9a-f]{64}").matches(templateSha256))
        require(runtimeRevision.isNotBlank() && backend.isNotBlank())
        require(runtimeBinarySha256==null || Regex("[0-9a-f]{64}").matches(runtimeBinarySha256))
    }
}

interface GeneratorTokenizer {
    fun tokenize(text: String, addSpecial: Boolean = false): IntArray
    fun renderTokens(system: String, user: String): IntArray
}

/** Owned raw buffer stays in memory; the consumer clears it in finally after validation.
 * Stop codes preserve the pinned JNI contract: 0=terminal, 1=cap, 2=cancelled.
 * Timings are model-token timings and must not be relabeled time to a visible answer.
 */
interface GenerationResult {
    val buffer: ByteArray
    val emitted: IntArray
    val stop: Int
    val prefillMs: Double
    val decodeWallMs: Double
    val firstEmittedTokenMs: Double
    val totalMs: Double
}

/** Serialized generation; cancellation may be called from a different thread.
 * close/cancel are idempotent; use after close must reject. Exact token/template
 * budgeting belongs to the consumer. No UI token streaming or tools are exposed.
 */
interface GeneratorBackend : GeneratorTokenizer, Closeable {
    val generationPolicy:GenerationPolicy get()=GenerationPolicy.BASELINE
    val identity: GeneratorIdentity
    val isGenerating: Boolean
    val loadAndVerificationMs: Double
    fun generate(tokens: IntArray, maximum: Int, cancelled: () -> Boolean = { false }): GenerationResult
    fun generate(request:GenerationRequest,cancelled:()->Boolean = {false}):GenerationResult {
        check(!request.policy.quoted){"GUIDED_GENERATION_UNSUPPORTED"}
        return generate(request.tokens,request.maximum,cancelled)
    }
    fun cancel()
}
