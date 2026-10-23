package org.packrag.product

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import org.json.JSONObject
import org.packrag.runtime.RuntimeTrace

/** Completed captured metadata only. No raw buffer, live reader or retrieval rerun. */
@Composable fun DiagnosticsPanel(trace:RuntimeTrace) {
    Text("Completed query diagnostics",style=MaterialTheme.typography.titleLarge,modifier=Modifier.testTag("completed-diagnostics"))
    Text("These are captured functional measurements. First emitted tokens may be reasoning; remaining emission includes terminal tokens. Session time excludes queue waiting, session construction and UI display. Missing measurements remain unknown. No visible-answer latency, peak memory, throughput or thermal conclusion is inferred.")
    diagnosticLines(trace).forEach { Text("${it.label}: ${it.value}") }
    val context=trace.diagnostics?.context
    context?.let {
        Text("Captured question: ${it.query.raw}")
        Text("Captured date: ${it.query.asOf} · jurisdiction: ${it.query.jurisdiction ?: "all"} · current law only: ${it.query.currentLaw}")
        Text("Captured limits: context ${it.profile.context}; prefill ${it.profile.prefill}; emitted ${it.profile.generated}; evidence ${it.profile.evidence}; chunks ${it.profile.chunks}; graph ${it.profile.graph}")
        it.identities.zip(it.manifests).forEach { (identity,manifest) ->
            Text("Captured active version: ${identity.packId}@${identity.version} · ${identity.manifestSha256}")
            Text("Signed embedder profile assertion: ${JSONObject(manifest).getJSONObject("embedding_profile")}")
        }
    }
    trace.session?.configured?.let {
        Text("Configured model: ${it.modelId} · ${it.artifact}")
        Text("Configured quantization: ${it.quantization}")
        Text("Configured embedder compatibility profile: ${it.embedderProfileJson}")
        Text("Source-weight identity in the profile is a build assertion. The deployed ONNX model/tokenizer hashes are checked at construction; this is not release calibration.")
    }
    val generator=context?.generator ?: trace.session?.generator
    if(generator==null) Text("Constructor-verified generator identity: Not initialized") else {
        Text("Constructor-verified GGUF SHA-256: ${generator.modelSha256}")
        Text("Constructor-verified template SHA-256: ${generator.templateSha256}")
        Text("llama.cpp revision: ${generator.runtimeRevision} · backend: ${generator.backend}")
        Text("Configured native-library SHA-256 pin (actual APK checked during acceptance): ${generator.runtimeBinarySha256 ?: "Unknown"}")
    }
    val candidates=trace.diagnostics?.candidates
    if(candidates==null) Text("Candidate collection did not return.") else {
        Text("Returned capped/deduplicated candidate pool (${candidates.size})",style=MaterialTheme.typography.titleMedium)
        candidates.forEachIndexed { index,row ->
            Text("Candidate ${index+1}: ${row.identity.packId}@${row.identity.version} · ${row.chunkId}",modifier=Modifier.testTag("diagnostic-candidate-$index"))
            Text("Manifest ${row.identity.manifestSha256} · source ${row.sourceId} · canonical ${row.canonicalSha256} · original ${row.originalSha256}")
            Text("Fused rank ${row.finalRank ?: "Unknown"}; sparse ${row.sparseRank ?: "None"}; dense ${row.denseRank ?: "None"}; cosine ${row.cosine}; RRF ${row.rrf}")
            Text("Identifier priority ${row.exact}; relevance admission ${row.relevant}; selection ${candidateSelection(trace,row.key)}")
            row.origins.forEachIndexed { originIndex,origin ->
                Text("Candidate ${index+1} origin ${originIndex+1}: ${origin.identity.packId}@${origin.identity.version} · ${origin.identity.manifestSha256} · ${origin.chunk.id}")
                Text("Origin ranks/scores: sparse ${origin.sparseRank ?: "None"}; dense ${origin.denseRank ?: "None"}; cosine ${origin.cosine}; RRF ${origin.rrf}; identifier ${origin.exact}")
                Text("Origin calibration assertion: ${origin.calibration.status}; agreed ${origin.calibration.agreed ?: "Unknown"}; dense-only ${origin.calibration.denseOnly ?: "Unknown"}. Representative candidate relevance is not an independently measured origin flag.")
            }
        }
    }
}
