package org.packrag.embedding

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import java.io.File
import java.nio.LongBuffer
import kotlin.math.sqrt

/** Local hash-pinned FP32 CPU encoder, CLS pooling followed by L2 normalization. */
class GraniteEncoder(assets: File, tokenizerHash: String, modelHash: String) : AutoCloseable {
    val tokenizer = GraniteTokenizer(File(assets, "tokenizer.json"), tokenizerHash)
    private val environment = OrtEnvironment.getEnvironment()
    private val session: OrtSession

    init {
        val model = File(assets, "onnx/model.onnx")
        require(fileSha256(model) == modelHash) { "ONNX model asset hash mismatch" }
        OrtSession.SessionOptions().use { options ->
            options.setIntraOpNumThreads(4)
            options.setInterOpNumThreads(1)
            session = environment.createSession(model.absolutePath, options)
        }
        require(session.inputNames == setOf("input_ids", "attention_mask"))
        require(session.outputNames == setOf("last_hidden_state"))
    }

    @Synchronized fun encode(text: String): FloatArray {
        val ids = tokenizer.encode(text)
        require(ids.size <= 512) { "EMBEDDING_INPUT_TOO_LONG" }
        val shape = longArrayOf(1, ids.size.toLong())
        OnnxTensor.createTensor(environment, LongBuffer.wrap(ids.map { it.toLong() }.toLongArray()), shape).use { input ->
            OnnxTensor.createTensor(environment, LongBuffer.wrap(LongArray(ids.size) { 1L }), shape).use { mask ->
                session.run(mapOf("input_ids" to input, "attention_mask" to mask)).use { result ->
                    @Suppress("UNCHECKED_CAST")
                    val hidden = result[0].value as Array<Array<FloatArray>>
                    val vector = hidden[0][0].copyOf()
                    require(vector.size == 384 && vector.all { it.isFinite() })
                    val norm = sqrt(vector.sumOf { it.toDouble() * it }).toFloat()
                    require(norm > 0)
                    return FloatArray(384) { vector[it] / norm }
                }
            }
        }
    }

    @Synchronized override fun close() { session.close() }
}
