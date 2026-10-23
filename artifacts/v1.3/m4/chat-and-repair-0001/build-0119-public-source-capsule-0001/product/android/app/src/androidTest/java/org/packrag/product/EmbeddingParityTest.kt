package org.packrag.product

import android.content.pm.PackageManager
import android.os.Build
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import kotlin.math.abs
import kotlin.math.sqrt
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.embedding.GraniteEncoder

@RunWith(AndroidJUnit4::class)
class EmbeddingParityTest {
    @Test fun noInternetCapabilityAndExactEmbeddingParity() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        val permissions = context.packageManager.getPackageInfo(context.packageName, PackageManager.GET_PERMISSIONS).requestedPermissions
        assertFalse(permissions?.contains("android.permission.INTERNET") ?: false)
        assertTrue(Build.SUPPORTED_ABIS.contains("arm64-v8a"))
        val reference = instrumentation.context.assets.open("parity-reference.json").bufferedReader(Charsets.UTF_8)
            .use { JSONObject(it.readText()) }
        val hashes = reference.getJSONObject("lock").getJSONObject("embedder").getJSONObject("asset_sha256")
        val assets = File(context.filesDir, "models/granite")
        val runtime = Runtime.getRuntime()
        val before = runtime.totalMemory() - runtime.freeMemory()
        val start = System.nanoTime()
        val results = JSONArray()
        GraniteEncoder(assets, hashes.getString("tokenizer.json"), hashes.getString("onnx/model.onnx")).use { encoder ->
            val loaded = (System.nanoTime() - start) / 1e6
            val tokenCases = reference.getJSONArray("tokenizer_cases")
            for (index in 0 until tokenCases.length()) {
                val case = tokenCases.getJSONObject(index)
                val ids = case.getJSONArray("ids")
                assertArrayEquals(case.getString("id"), IntArray(ids.length()) { ids.getInt(it) }, encoder.tokenizer.encode(case.getString("text")))
            }
            val cases = reference.getJSONArray("embedding_cases")
            for (index in 0 until cases.length()) {
                val case = cases.getJSONObject(index)
                val tick = System.nanoTime()
                val actual = encoder.encode(case.getString("text"))
                val expected = case.getJSONArray("vector")
                val maximum = actual.indices.maxOf { abs(actual[it] - expected.getDouble(it)) }
                val dot = actual.indices.sumOf { actual[it].toDouble() * expected.getDouble(it) }
                val actualNorm = sqrt(actual.sumOf { it.toDouble() * it })
                val expectedNorm = sqrt((0 until expected.length()).sumOf { expected.getDouble(it) * expected.getDouble(it) })
                val cosine = dot / (actualNorm * expectedNorm)
                assertTrue("embedding maximum error $maximum", maximum <= 1e-4)
                assertTrue("embedding cosine $cosine", cosine >= .99999)
                results.put(JSONObject().put("text", case.getString("text")).put("max_abs_error", maximum)
                    .put("cosine", cosine).put("latency_ms", (System.nanoTime() - tick) / 1e6)
                    .put("vector", JSONArray(actual.toList())))
            }
            File(context.filesDir, "m2-embedding-parity.json").writeText(
                JSONObject().put("status", "PASS").put("tokenizer_cases", tokenCases.length()).put("embedding_cases", results)
                    .put("model", Build.MODEL).put("sdk", Build.VERSION.SDK_INT).put("java_vm", System.getProperty("java.vm.name"))
                    .put("initialization_ms", loaded)
                    .put("java_heap_delta_at_end_bytes", runtime.totalMemory() - runtime.freeMemory() - before)
                    .put("purpose", "M2_COMPONENT_PARITY_NOT_FULL_ANDROID_E2E_OR_PERFORMANCE_ACCEPTANCE").toString(2), Charsets.UTF_8)
        }
    }
}
