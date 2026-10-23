package org.packrag.week1

data class ModelInfo(val modelHash: String, val backendName: String, val quantization: String)
data class GenerationResult(val text: String, val promptTokens: Int, val generatedTokens: Int,
    val timeToFirstTokenMs: Double, val totalLatencyMs: Double, val averageTokensPerSecond: Double,
    val modelHash: String, val backendName: String, val quantization: String)

interface GeneratorBackend : AutoCloseable {
    fun load(modelPath: String): ModelInfo
    /** Returns complete buffered generation; callers validate before display. */
    fun generate(prompt: String, maxNewTokens: Int = 256, temperature: Float = 0f,
                 topP: Float = 1f, stopStrings: List<String> = emptyList()): GenerationResult
    override fun close()
}

object OutputValidator {
    fun acceptedBody(text: String, suppliedIds: Set<String>): String? {
        if (text == "INSUFFICIENT_EVIDENCE") return null
        val ids = Regex("\\[(S\\d+)\\]").findAll(text).map { it.groupValues[1] }.toList()
        if (ids.isEmpty() || ids.any { it !in suppliedIds }) return null
        if (text.split(Regex("\\n\\s*\\n")).filter { it.isNotBlank() }.any { !Regex("\\[S\\d+\\]").containsMatchIn(it) }) return null
        if (Regex("</?(SYSTEM|ANSWER|QUESTION|CONTEXT|VERIFIED_EVIDENCE)\\b").containsMatchIn(text)) return null
        return text // Syntax only; semantic support remains an evaluation metric.
    }
}
