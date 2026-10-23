package org.packrag.product

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID
import kotlin.math.abs
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.embedding.GraniteEncoder
import org.packrag.generator.LlamaGenerator
import org.packrag.model.DerivedText
import org.packrag.model.GeneratorRepresentation
import org.packrag.model.GeneratorRepresentations
import org.packrag.model.Query
import org.packrag.model.RepresentationFailure
import org.packrag.model.SourceText
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier
import org.packrag.retrieval.Retrieval
import org.packrag.runtime.Prompt

/** Presence and signed-byte preservation; metadata labels do not establish real review. */
@RunWith(AndroidJUnit4::class)
class SourceTextDeviceTest {
    @Test fun fixedPresenceAllScalarsResolverSignedImportsAndActualTokenizer() {
        val instrument=InstrumentationRegistry.getInstrumentation();val context=instrument.targetContext;val assets=instrument.context.assets
        val reference=assets.open("source-text-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val fixedBytes=assets.open("source-text-corpus/source-text-contracts.json").use { it.readBytes() }
        assertEquals(reference.getString("fixed_contract_sha256"),Crypto.sha256(fixedBytes))
        val fixed=JSONObject(fixedBytes.toString(Charsets.UTF_8));val cases=fixed.getJSONArray("cases");assertEquals(38,cases.length())
        for(i in 0 until cases.length()) { val row=cases.getJSONObject(i)
            assertEquals(row.getString("id"),row.getBoolean("expected_nonblank"),SourceText.nonBlank(if(row.isNull("value")) null else row.getString("value"))) }
        val points=fixed.getJSONArray("whitespace_points");val whitespace=(0 until points.length()).map { points.getInt(it) }.toSet();assertEquals(29,whitespace.size)
        var scalars=0
        for(point in 0..0x10ffff) { if(point in 0xd800..0xdfff)continue
            assertEquals("U+${point.toString(16)}",point !in whitespace,SourceText.nonBlank(String(Character.toChars(point))));scalars++ }
        assertEquals(1112064,scalars)
        var resolverChecks=0
        for(point in whitespace) for(field in listOf("canonical","text","derivation_source","reviewer_id")) {
            val blank=String(Character.toChars(point));val canonical=if(field=="canonical") blank else "Source."
            val body=if(field=="text") blank else "74 °C."
            val row=DerivedText("c","generator","en",body,Crypto.sha256(body.toByteArray(Charsets.UTF_8)),"human_reviewed_translation",if(field=="derivation_source") blank else "SYNTHETIC",if(field=="reviewer_id") blank else "SYNTHETIC","2026-10-09")
            val result=runCatching { GeneratorRepresentations.select(canonical,Crypto.sha256(canonical.toByteArray(Charsets.UTF_8)),if(field=="canonical") "en" else "fr",listOf(row)) }
            assertEquals(field+":"+point,"INVALID_GENERATOR_PROVENANCE",(result.exceptionOrNull() as RepresentationFailure).state);resolverChecks++
        }
        assertEquals(116,resolverChecks)
        val public=assets.open("source-text-corpus/public-key.raw").use { it.readBytes() };assertEquals(reference.getString("public_key_sha256"),Crypto.sha256(public))
        val lock=context.assets.open("toolchain.lock.json").bufferedReader().use { JSONObject(it.readText()) }.getJSONObject("embedder")
        val schema=context.assets.open("schema.sql").bufferedReader().use { it.readText() }
        val root=File(context.filesDir,"source-text-parity-${UUID.randomUUID()}");assertTrue(root.mkdirs());val imports=JSONArray();val tokens=JSONArray()
        try {
            PackRegistry(File(root,"registry"),PackVerifier(listOf(public),lock.getJSONObject("pack_profile"),schema,true)).use { registry ->
                val records=reference.getJSONArray("packs");assertEquals(6,records.length())
                val hashes=lock.getJSONObject("asset_sha256");val models=File(context.filesDir,"models")
                GraniteEncoder(File(models,"granite"),hashes.getString("tokenizer.json"),hashes.getString("onnx/model.onnx")).use { encoder ->
                    LlamaGenerator(File(models,"LFM2.5-2.6B-QAD-Q4_0.gguf"),File(models,"chat_template.jinja"),vocabularyOnly=true).use { tokenizer ->
                        val query=Query(reference.getString("raw"),reference.getString("as_of"));assertEquals(reference.getString("normalized"),query.normalized)
                        val vector=encoder.encode(query.normalized);val stored=reference.getJSONArray("query_vector")
                        var maxEmbedding=0.0;for(j in vector.indices)maxEmbedding=maxOf(maxEmbedding,abs(vector[j]-stored.getDouble(j)));assertTrue(maxEmbedding<=1e-4)
                        for(i in 0 until records.length()) {
                            val row=records.getJSONObject(i);val label=row.getString("id");val archive=File(root,row.getString("filename"))
                            assets.open("source-text-corpus/"+archive.name).use { input -> archive.outputStream().use { input.copyTo(it) } };assertEquals(row.getString("sha256"),Crypto.fileHash(archive))
                            val imported=runCatching { registry.activate(archive) }
                            val observation=JSONObject().put("id",label).put("accepted",imported.isSuccess).put("error",imported.exceptionOrNull()?.message ?: JSONObject.NULL)
                            File(context.filesDir,"m4-source-text-import-observed.json").writeText(observation.toString(2),Charsets.UTF_8)
                            assertEquals(label,row.getBoolean("accept"),imported.isSuccess);imports.put(observation)
                            if(!row.getBoolean("accept")) { assertTrue(registry.snapshot().isEmpty());continue }
                            val pack=imported.getOrThrow();val retrieved=Retrieval.retrieve(listOf(pack),query,vector);assertFalse(retrieved.ambiguous);assertEquals(1,retrieved.candidates.size)
                            val candidate=retrieved.candidates.single();assertTrue(candidate.exact && candidate.relevant)
                            assertEquals(row.getString("canonical_text"),candidate.chunk.canonicalText);assertEquals(row.getString("canonical_text_sha256"),candidate.chunk.textSha256);assertEquals("fr",candidate.chunk.language)
                            val prompt=Prompt.prepare(query,listOf(pack),retrieved.candidates,tokenizer)
                            val actual=sourceTextRepresentationJson(prompt.representations.single());val expected=row.getJSONObject("generator_representation")
                            val record=JSONObject().put("id",label).put("status","OBSERVED_NOT_ACCEPTANCE").put("admission","READY").put("max_embedding_abs_error",maxEmbedding)
                                .put("actual_tokenizer",JSONObject().put("tokens",JSONArray(prompt.tokens.toList())).put("prefill_tokens",prompt.tokens.size).put("evidence_tokens",prompt.evidenceTokens).put("max_new",prompt.maximum).put("selected",JSONArray(prompt.evidence.map { it.chunk.id })))
                                .put("representations",JSONArray().put(actual)).put("canonical_text",candidate.chunk.canonicalText).put("canonical_text_sha256",candidate.chunk.textSha256)
                            File(context.filesDir,"m4-source-text-tokenizer-observed.json").writeText(record.toString(2),Charsets.UTF_8)
                            assertEquals(expected.keys().asSequence().toSet(),actual.keys().asSequence().toSet());for(key in expected.keys())assertEquals(key,expected.get(key),actual.get(key))
                            assertTrue(prompt.tokens.size<=1536 && prompt.evidenceTokens<=1200 && prompt.evidence.size==1 && prompt.maximum<=512)
                            record.put("status","PASS");tokens.put(record);registry.deactivate(pack.id)
                            File(context.filesDir,"m4-source-text-progress.json").writeText(JSONObject().put("status","RUNNING").put("imports",imports).put("tokenizer_cases",tokens).toString(2),Charsets.UTF_8)
                        }
                    }
                }
            }
            assertEquals(6,imports.length());assertEquals(2,tokens.length())
            File(context.filesDir,"m4-source-text.json").writeText(JSONObject().put("status","PASS").put("fixed_presence_cases",38).put("whitespace_points",29).put("valid_scalars_checked",scalars).put("blank_resolver_checks",resolverChecks)
                .put("imports",imports).put("tokenizer_cases",tokens).put("purpose","PRESENCE_BYTE_PRESERVATION_ACTUAL_GRANITE_AND_GGUF_TOKENIZER_NOT_WEIGHT_INFERENCE_OR_REAL_REVIEW")
                .put("developer_trust","EXPLICIT_ISOLATED_TEST_KEYS_NOT_PRODUCTION_DEFAULT").toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));root.deleteRecursively() }
    }
}

private fun sourceTextRepresentationJson(r:GeneratorRepresentation):JSONObject=JSONObject().put("text",r.text).put("language",r.language)
    .put("text_sha256",r.textSha256).put("derivation_method",r.derivationMethod).put("derivation_source",r.derivationSource ?: JSONObject.NULL)
    .put("reviewer_id",r.reviewerId ?: JSONObject.NULL).put("reviewed_at",r.reviewedAt ?: JSONObject.NULL)
    .put("canonical_language",r.canonicalLanguage).put("canonical_text_sha256",r.canonicalTextSha256)
