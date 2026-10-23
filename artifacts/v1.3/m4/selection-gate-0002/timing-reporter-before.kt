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
import org.packrag.generator.GeneratorBackend
import org.packrag.generator.GeneratorIdentity
import org.packrag.generator.GenerationResult
import org.packrag.generator.LlamaGenerator
import org.packrag.model.*
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier
import org.packrag.retrieval.Retrieval
import org.packrag.runtime.AdmissionFailure
import org.packrag.runtime.PackRag
import org.packrag.runtime.Prompt

/** Isolated synthetic protocol controls, never owner release content or held-out gold. */
@RunWith(AndroidJUnit4::class)
class SelectionDeviceTest {
    private val instrument get()=InstrumentationRegistry.getInstrumentation()
    private val context get()=instrument.targetContext
    private val assets get()=instrument.context.assets
    private fun reference()=assets.open("selection-corpus/cases.json").bufferedReader().use { JSONObject(it.readText()) }
    private fun formatCase()=assets.open("selection-corpus/format-control.json").bufferedReader().use { JSONObject(it.readText()) }
    private fun publicKey()=assets.open("selection-corpus/public-key.raw").use { it.readBytes() }
    private fun lock()=context.assets.open("toolchain.lock.json").bufferedReader().use { JSONObject(it.readText()) }
    private fun encoder():GraniteEncoder {
        val hashes=lock().getJSONObject("embedder").getJSONObject("asset_sha256")
        return GraniteEncoder(File(context.filesDir,"models/granite"),hashes.getString("tokenizer.json"),hashes.getString("onnx/model.onnx"))
    }
    private fun generator(vocabularyOnly:Boolean=false)=LlamaGenerator(File(context.filesDir,"models/LFM2.5-2.6B-QAD-Q4_0.gguf"),
        File(context.filesDir,"models/chat_template.jinja"),vocabularyOnly=vocabularyOnly)
    private fun registry(root:File)=PackRegistry(File(root,"registry"),PackVerifier(listOf(publicKey()),
        lock().getJSONObject("embedder").getJSONObject("pack_profile"),context.assets.open("schema.sql").bufferedReader().use { it.readText() },true))
    private fun archive(root:File,row:JSONObject):File {
        val file=File(root,row.getString("filename"))
        assets.open("selection-corpus/"+file.name).use { input -> file.outputStream().use { input.copyTo(it) } }
        assertEquals(row.getString("sha256"),Crypto.fileHash(file));return file
    }
    private fun save(name:String,row:JSONObject)=File(context.filesDir,name).writeText(row.toString(2),Charsets.UTF_8)
    private fun query(row:JSONObject)=Query(row.getString("raw"),row.getString("as_of"),if(row.isNull("jurisdiction")) null else row.getString("jurisdiction"))
    private fun root(label:String)=File(context.filesDir,"selection-$label-${UUID.randomUUID()}").also { assertTrue(it.mkdirs()) }
    private fun remove(root:File) { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));assertTrue(root.deleteRecursively()) }

    @Test fun fixedPlansSignedActualTokenizerAndOwnedEvidence() {
        val ref=reference();val fixedBytes=assets.open("selection-corpus/selection-contracts.json").use { it.readBytes() }
        assertEquals(ref.getString("fixed_contract_sha256"),Crypto.sha256(fixedBytes))
        assertEquals(ref.getString("public_key_sha256"),Crypto.sha256(publicKey()))
        val fixed=JSONObject(fixedBytes.toString(Charsets.UTF_8)).getJSONArray("cases");assertEquals(28,fixed.length())
        for(i in 0 until fixed.length())selectionFixedCase(fixed.getJSONObject(i))
        val results=JSONArray();val root=root("tokenizer");var dedup=JSONObject()
        try {
            registry(root).use { registry -> encoder().use { encoder -> generator(true).use { tokenizer ->
                val cases=ref.getJSONArray("cases");val records=ref.getJSONArray("packs");assertEquals(8,cases.length())
                val all=(0 until cases.length()).map { cases.getJSONObject(it) }+formatCase();val installed=mutableMapOf<String,PackIdentity>()
                for(case in all) {
                    val label=case.getString("id");val packLabel=if(label=="atomic-format-control") "atomic-last" else label
                    val record=(0 until records.length()).map { records.getJSONObject(it) }.single { it.getString("id")==packLabel }
                    val pack=installed[packLabel]?.let { registry.activateInstalled(it.packId,it.version) }
                        ?: registry.activate(archive(root,record)).also { installed[packLabel]=PackIdentity(it.id,it.version,it.manifestHash) }
                    val query=query(case);val vector=encoder.encode(query.normalized)
                    val expected=case.getJSONArray("query_vector");var error=0.0
                    for(j in vector.indices)error=maxOf(error,abs(vector[j]-expected.getDouble(j)))
                    assertTrue(label+": embedding",error<=1e-4)
                    val pool=Retrieval.retrieve(listOf(pack),query,vector);assertFalse(pool.ambiguous)
                    assertEquals(strings(case.getJSONArray("expected_pool")),pool.candidates.map { it.chunk.id })
                    assertEquals((1..pool.candidates.size).toList(),pool.candidates.map { it.finalRank })
                    for(candidate in pool.candidates) {
                        val origin=candidate.originRecords.single();assertEquals(candidate.chunk,origin.chunk)
                        assertEquals(candidate.packIdentity,origin.identity);assertEquals(candidate.sparseRank,origin.sparseRank)
                        assertEquals(candidate.denseRank,origin.denseRank);assertEquals(candidate.rrf,origin.rrf,0.0)
                    }
                    val observed=JSONObject().put("id",label).put("status","OBSERVED_NOT_ACCEPTANCE").put("max_embedding_abs_error",error)
                        .put("candidates",JSONArray(pool.candidates.map { candidate -> JSONObject().put("chunk_id",candidate.chunk.id)
                            .put("fused_rank",candidate.finalRank).put("cosine",candidate.cosine).put("rrf",candidate.rrf)
                            .put("origins",JSONArray(candidate.originRecords.map(::originJson))) }))
                    try {
                        val inputOrigins=pool.candidates.map { it.originRecords.toMutableList() }
                        val inputs=pool.candidates.mapIndexed { j,candidate -> candidate.copy(originRecords=inputOrigins[j]) }
                        val prepared=Prompt.prepare(query,listOf(pack),inputs,tokenizer)
                        val reversed=Prompt.prepare(query,listOf(pack),inputs.reversed(),tokenizer)
                        assertArrayEquals(prepared.tokens,reversed.tokens);assertEquals(prepared.selection,reversed.selection)
                        val tokens=prepared.tokens;tokens.fill(-1);assertTrue(prepared.tokens.all { it>=0 })
                        val original=prepared.evidence.map { evidenceJson(it).toString() }
                        inputOrigins.forEach { it.clear() };pack.manifest.getJSONObject("publisher").put("diagnostic_after_prepare","changed")
                        assertEquals(original,prepared.evidence.map { evidenceJson(it).toString() })
                        assertThrows(UnsupportedOperationException::class.java) { (prepared.evidence as MutableList).clear() }
                        assertThrows(UnsupportedOperationException::class.java) { (prepared.selection.decisions.first().trial as MutableList).clear() }
                        observed.put("admission","READY").put("selection",selectionJson(prepared.selection))
                            .put("actual_tokenizer",JSONObject().put("tokens",JSONArray(prepared.tokens.toList())).put("prefill_tokens",prepared.tokens.size)
                                .put("evidence_tokens",prepared.evidenceTokens).put("max_new",prepared.maximum).put("selected",JSONArray(prepared.evidence.map { it.chunk.id })))
                            .put("evidence",JSONArray(prepared.evidence.map(::evidenceJson)))
                    } catch(failure:AdmissionFailure) { observed.put("admission",failure.state).put("selection",failure.selection?.let(::selectionJson) ?: JSONObject.NULL) }
                    save("m4-selection-tokenizer-observed.json",observed)
                    assertEquals(label,case.getString("expected_admission"),observed.getString("admission"))
                    val plan=observed.getJSONObject("selection");assertEquals(pool.candidates.size,plan.getJSONArray("decisions").length())
                    if(observed.getString("admission")=="READY") {
                        val actual=observed.getJSONObject("actual_tokenizer");val expectedTokens=case.getJSONObject("actual_tokenizer")
                        for(key in listOf("tokens","selected"))assertEquals(label+": "+key,expectedTokens.getJSONArray(key).toString(),actual.getJSONArray(key).toString())
                        for(key in listOf("prefill_tokens","evidence_tokens","max_new"))assertEquals(expectedTokens.getInt(key),actual.getInt(key))
                    } else { assertTrue(strings(plan.getJSONArray("keys")).isEmpty());assertEquals(case.getString("expected_admission"),plan.getString("admission")) }
                    observed.put("status","PASS");results.put(observed);registry.deactivate(pack.id)
                    save("m4-selection-tokenizer-progress.json",JSONObject().put("status","RUNNING").put("cases",results))
                }
                dedup=dedupOriginControl(root,encoder,tokenizer)
            } } }
            save("m4-selection-tokenizer.json",JSONObject().put("status","PASS").put("fixed_plans",28).put("signed_tokenizer_cases",8)
                .put("post_observation_format_controls",1).put("deduplicated_origin_control",dedup).put("cases",results).put("scope","SYNTHETIC_PROTOCOL_NOT_OWNER_CONTENT_OR_GOLD"))
        } finally { remove(root) }
    }

    private fun dedupOriginControl(root:File,encoder:GraniteEncoder,tokenizer:LlamaGenerator):JSONObject {
        val corpus=assets.open("query-identifier-corpus/cases.json").bufferedReader().use { JSONObject(it.readText()) }
        val cases=corpus.getJSONArray("cases");val case=(0 until cases.length()).map { cases.getJSONObject(it) }.single { it.getString("id")=="WITHIN_PACK_DEDUP_ORIGIN_UNIQUE" }
        val packs=corpus.getJSONArray("packs");val record=(0 until packs.length()).map { packs.getJSONObject(it) }.single { it.getString("id")=="within-duplicate" }
        val public=assets.open("query-identifier-corpus/public-key.raw").use { it.readBytes() }
        val slot=File(root,"dedup");assertTrue(slot.mkdirs());val archive=File(slot,record.getString("filename"))
        assets.open("query-identifier-corpus/"+archive.name).use { input -> archive.outputStream().use { input.copyTo(it) } }
        assertEquals(record.getString("sha256"),Crypto.fileHash(archive))
        PackRegistry(File(slot,"registry"),PackVerifier(listOf(public),lock().getJSONObject("embedder").getJSONObject("pack_profile"),
            context.assets.open("schema.sql").bufferedReader().use { it.readText() },true)).use { registry ->
            val pack=registry.activate(archive);val query=Query(case.getString("raw"),case.getString("as_of"))
            val pool=Retrieval.retrieve(listOf(pack),query,encoder.encode(query.normalized));assertFalse(pool.ambiguous)
            val candidate=pool.candidates.single();assertEquals(1,candidate.origins.size);assertEquals(2,candidate.originRecords.size)
            assertEquals(pack.chunks.map { it.id }.toSet(),candidate.originRecords.map { it.chunk.id }.toSet())
            assertEquals(setOf("first","second"),candidate.originRecords.map { it.chunk.locator }.toSet())
            val prepared=Prompt.prepare(query,listOf(pack),pool.candidates,tokenizer);assertEquals(candidate.originRecords,prepared.evidence.single().originRecords)
            return JSONObject().put("status","PASS").put("id",case.getString("id")).put("pack_sha256",record.getString("sha256"))
                .put("origin_records",JSONArray(prepared.evidence.single().originRecords.map(::originJson)))
        }
    }

    @Test fun actualLfmAtomicBundleAndDeterministicAdmissionOrOutputRejection() {
        val ref=reference();val records=ref.getJSONArray("packs");val cases=ref.getJSONArray("cases");val results=JSONArray();val root=root("runtime")
        try {
            registry(root).use { registry -> encoder().use { encoder -> generator().use { backend ->
                val generator=SelectionCountingBackend(backend);val runtime=PackRag(registry,encoder,generator)
                val labels=listOf("atomic-last","five-mandatory","missing-global","mandatory-oversize","optional-oversize","all-oversize","boundary1201","atomic-format-control")
                val installed=mutableMapOf<String,PackIdentity>()
                for(label in labels) {
                    val case=if(label=="atomic-format-control") formatCase() else (0 until cases.length()).map { cases.getJSONObject(it) }.single { it.getString("id")==label }
                    val packLabel=if(label=="atomic-format-control") "atomic-last" else label
                    val record=(0 until records.length()).map { records.getJSONObject(it) }.single { it.getString("id")==packLabel }
                    val pack=installed[packLabel]?.let { registry.activateInstalled(it.packId,it.version) }
                        ?: registry.activate(archive(root,record)).also { installed[packLabel]=PackIdentity(it.id,it.version,it.manifestHash) }
                    val before=generator.calls;val trace=runtime.ask(query(case))
                    val expected=if(label=="atomic-last") "OUTPUT_REJECTED" else if(label=="atomic-format-control") "ANSWER_ACCEPTED" else case.getString("expected_admission")
                    val observed=JSONObject().put("id",label).put("status","OBSERVED_NOT_ACCEPTANCE").put("state",trace.answer.state)
                        .put("expected_state",expected).put("answer",trace.answer.text ?: JSONObject.NULL).put("generate_calls",generator.calls-before)
                        .put("selected",JSONArray(trace.selected)).put("evidence",JSONArray(trace.evidence.map(::evidenceJson)))
                        .put("selection",trace.selection?.let(::selectionJson) ?: JSONObject.NULL).put("sources",JSONArray(trace.answer.sources.map { source ->
                            JSONObject().put("id",source.evidenceId).put("chunk_id",source.chunkId).put("original_sha256",source.originalSha256)
                                .put("canonical_text",source.canonicalText).put("canonical_text_sha256",source.canonicalTextSha256).put("source_id",source.sourceId)
                                .put("fused_rank",source.fusedRank).put("identity",identityJson(source.pack)).put("origin_records",JSONArray(source.originRecords.map(::originJson))) }))
                        .put("prefill_tokens",trace.prefillTokens).put("evidence_tokens",trace.evidenceTokens).put("emitted_tokens_including_terminal",trace.emittedTokens)
                        .put("total_ms_including_initialization_not_benchmark",trace.totalMs)
                        .put("scope",if(label=="atomic-last") "POST_OBSERVATION_REJECTION_REGRESSION_ORIGINAL_ACCEPTANCE_FAILED" else if(label=="atomic-format-control") "POST_OBSERVATION_FORMAT_CONTROL_NOT_HELDOUT" else "PRE_GENERATION_PROTOCOL_CONTROL")
                    save("m4-selection-runtime-observed.json",observed);assertEquals(label,expected,trace.answer.state)
                    if(label in listOf("atomic-last","atomic-format-control")) {
                        assertEquals(before+1,generator.calls);assertEquals(strings(case.getJSONArray("expected_selected")),trace.selected)
                        assertEquals(listOf(1,2,3,5),trace.evidence.map { it.finalRank });assertTrue(trace.emittedTokens in 1..512)
                        if(expected=="ANSWER_ACCEPTED") {
                            assertTrue(trace.answer.text!!.contains("74 °C"));assertFalse(trace.answer.text!!.contains("</think>"));assertEquals(4,trace.answer.sources.size)
                            for(source in trace.answer.sources) {
                                val frozen=trace.evidence[source.evidenceId.drop(1).toInt()-1];assertEquals(frozen.packIdentity,source.pack)
                                assertEquals(frozen.chunk.canonicalText,source.canonicalText);assertEquals(frozen.chunk.id,source.chunkId)
                                assertEquals(frozen.chunk.originalSha256,source.originalSha256);assertEquals(frozen.originRecords,source.originRecords)
                            }
                        } else { assertNull(trace.answer.text);assertTrue(trace.answer.sources.isEmpty()) }
                    } else {
                        assertEquals(before,generator.calls);assertEquals(0,trace.emittedTokens);assertNull(trace.answer.text)
                        assertTrue(trace.selected.isEmpty() && trace.answer.sources.isEmpty());assertEquals(expected,trace.selection!!.admission)
                    }
                    observed.put("status","PASS");results.put(observed);registry.deactivate(pack.id)
                    save("m4-selection-runtime-progress.json",JSONObject().put("status","RUNNING").put("cases",results))
                }
            } } }
            save("m4-selection-runtime.json",JSONObject().put("status","PASS").put("cases",results).put("raw_reasoning_persisted",false)
                .put("network_mode","MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET").put("scope","REAL_LFM_SYNTHETIC_PROTOCOL_NOT_RELEASE_ACCURACY_OR_PERFORMANCE"))
        } finally { remove(root) }
    }

    @Test fun mutableManifestOrBackendIdentityCannotReachGeneration() {
        val ref=reference();val records=ref.getJSONArray("packs");val record=(0 until records.length()).map { records.getJSONObject(it) }.single { it.getString("id")=="atomic-last" }
        val results=JSONArray();val root=root("guards")
        try {
            encoder().use { encoder -> generator(true).use { backend ->
                for(target in listOf("manifest","backend")) {
                    val slot=File(root,target);assertTrue(slot.mkdirs())
                    registry(slot).use { registry ->
                        val pack=registry.activate(archive(slot,record));var changed=false
                        val wrapped=SelectionCountingBackend(backend) {
                            if(!changed) { changed=true;if(target=="manifest")pack.manifest.getJSONObject("publisher").put("diagnostic_before_generate","mutated") }
                        }
                        wrapped.mutateIdentity={ target=="backend" && changed }
                        val trace=PackRag(registry,encoder,wrapped).ask(query(formatCase()))
                        val observation=JSONObject().put("id",target).put("status","OBSERVED_NOT_ACCEPTANCE").put("state",trace.answer.state).put("generate_calls",wrapped.calls)
                        save("m4-selection-guards-observed.json",observation)
                        assertEquals(if(target=="manifest") "ACTIVE_PACK_CHANGED" else "GENERATOR_IDENTITY_CHANGED",trace.answer.state)
                        assertEquals(0,wrapped.calls);assertNull(trace.answer.text);assertTrue(trace.answer.sources.isEmpty())
                        observation.put("status","PASS");results.put(observation)
                    }
                }
            } }
            save("m4-selection-guards.json",JSONObject().put("status","PASS").put("cases",results).put("scope","IN_MEMORY_TRUSTED_STATE_SIMULATION_NOT_FILESYSTEM_RACE"))
        } finally { remove(root) }
    }
}

private class SelectionCountingBackend(private val backend:GeneratorBackend,private val onRender:()->Unit={}) : GeneratorBackend by backend {
    var calls=0
    var mutateIdentity:()->Boolean={ false }
    override val identity:GeneratorIdentity get()=if(mutateIdentity())backend.identity.copy(runtimeRevision=backend.identity.runtimeRevision+"-test-change") else backend.identity
    override fun renderTokens(system:String,user:String):IntArray { onRender();return backend.renderTokens(system,user) }
    override fun generate(tokens:IntArray,maximum:Int,cancelled:()->Boolean):GenerationResult { calls++;return backend.generate(tokens,maximum,cancelled) }
    override fun close() {} // The outer owner closes the actual backend once.
}
private fun strings(array:JSONArray)=(0 until array.length()).map { array.getString(it) }
private fun identityJson(value:PackIdentity)=JSONArray(listOf(value.packId,value.version,value.manifestSha256))
private fun selectionJson(plan:SelectionPlan)=JSONObject().put("admission",plan.admission).put("keys",JSONArray(plan.keys)).put("sources",JSONArray(plan.sources))
    .put("decisions",JSONArray(plan.decisions.map { decision -> JSONObject().put("key",decision.key).put("reason",decision.reason).put("trial",JSONArray(decision.trial))
        .put("representative",decision.representative ?: JSONObject.NULL).put("evidence_tokens",decision.evidenceTokens ?: JSONObject.NULL).put("prefill_tokens",decision.prefillTokens ?: JSONObject.NULL) }))
private fun chunkJson(c:Chunk)=JSONObject().put("chunk_id",c.id).put("source_id",c.sourceId).put("canonical_text",c.canonicalText).put("text_sha256",c.textSha256)
    .put("original_sha256",c.originalSha256).put("title",c.title).put("source_title",c.sourceTitle).put("section",c.section ?: JSONObject.NULL).put("locator",c.locator)
    .put("dense_row",c.denseRow).put("jurisdiction",c.jurisdiction ?: JSONObject.NULL).put("source_from",c.sourceFrom ?: JSONObject.NULL).put("source_until",c.sourceUntil ?: JSONObject.NULL)
    .put("effective_from",c.effectiveFrom ?: JSONObject.NULL).put("effective_until",c.effectiveUntil ?: JSONObject.NULL).put("legal_status",c.legalStatus ?: JSONObject.NULL)
    .put("publisher",c.publisher).put("canonical_uri",c.canonicalUri ?: JSONObject.NULL).put("language",c.language).put("authority_rank",c.authorityRank ?: JSONObject.NULL)
    .put("document_version",c.documentVersion ?: JSONObject.NULL).put("issued_at",c.issuedAt ?: JSONObject.NULL).put("article",c.article ?: JSONObject.NULL)
private fun metadataJson(m:SourceMetadata)=JSONObject().put("authority_rank",m.authorityRank ?: JSONObject.NULL).put("document_version",m.documentVersion ?: JSONObject.NULL)
    .put("issued_at",m.issuedAt ?: JSONObject.NULL).put("article",m.article ?: JSONObject.NULL).put("publisher_key_id",m.publisherKeyId)
    .put("relations",JSONArray(m.relations.map { JSONObject().put("from_chunk_id",it.fromChunkId).put("to_chunk_id",it.toChunkId).put("relation_type",it.relationType).put("provenance",it.provenance).put("confidence",it.confidence) }))
private fun conflictJson(c:ConflictDecision)=JSONObject().put("members",JSONArray(c.members)).put("state",c.state).put("preferred",c.preferred ?: JSONObject.NULL)
    .put("resolved",c.resolved).put("retained",JSONArray(c.retained)).put("required",JSONArray(c.required.map { JSONArray(listOf(it.first,it.second)) })).put("reason",c.reason)
private fun renderingJson(r:GeneratorRepresentation)=JSONObject().put("text",r.text).put("language",r.language).put("text_sha256",r.textSha256)
    .put("derivation_method",r.derivationMethod).put("derivation_source",r.derivationSource ?: JSONObject.NULL).put("reviewer_id",r.reviewerId ?: JSONObject.NULL)
    .put("reviewed_at",r.reviewedAt ?: JSONObject.NULL).put("canonical_language",r.canonicalLanguage).put("canonical_text_sha256",r.canonicalTextSha256)
private fun originJson(o:EvidenceOrigin)=JSONObject().put("identity",identityJson(o.identity)).put("chunk",chunkJson(o.chunk)).put("metadata",metadataJson(o.metadata))
    .put("derived",JSONArray(o.derived.map { JSONObject().put("chunk_id",it.chunkId).put("purpose",it.purpose).put("language",it.language).put("text",it.text).put("text_sha256",it.textSha256)
        .put("derivation_method",it.derivationMethod).put("derivation_source",it.derivationSource ?: JSONObject.NULL).put("reviewer_id",it.reviewerId ?: JSONObject.NULL).put("reviewed_at",it.reviewedAt ?: JSONObject.NULL) }))
    .put("exact",o.exact).put("sparse_rank",o.sparseRank ?: JSONObject.NULL).put("dense_rank",o.denseRank ?: JSONObject.NULL).put("cosine",o.cosine).put("rrf",o.rrf)
    .put("calibration",JSONObject().put("status",o.calibration.status).put("agreed",o.calibration.agreed ?: JSONObject.NULL).put("dense_only",o.calibration.denseOnly ?: JSONObject.NULL))
    .put("conflicts",JSONArray(o.conflicts.map(::conflictJson)))
private fun evidenceJson(e:FrozenEvidence)=JSONObject().put("identity",identityJson(e.packIdentity)).put("chunk",chunkJson(e.chunk)).put("source_metadata",metadataJson(e.metadata))
    .put("rendering",renderingJson(e.generatorRendering)).put("fused_rank",e.finalRank ?: JSONObject.NULL).put("exact",e.exact).put("relevant",e.relevant)
    .put("sparse_rank",e.sparseRank ?: JSONObject.NULL).put("dense_rank",e.denseRank ?: JSONObject.NULL).put("cosine",e.cosine).put("rrf",e.rrf)
    .put("origin_records",JSONArray(e.originRecords.map(::originJson))).put("conflicts",JSONArray(e.conflicts.map(::conflictJson)))
private fun selectionFixedCase(case:JSONObject) {
    val rows=case.getJSONArray("items")
    val labels=(0 until rows.length()).associate { i -> val r=rows.getJSONObject(i);r.getString("key") to (r.optString("source",r.getString("key")) to r.optString("canonical",r.getString("key"))) }
    val items=(0 until rows.length()).map { i -> val r=rows.getJSONObject(i);val key=r.getString("key");val required=r.optJSONArray("required")
        SelectionItem(key,r.optInt("position",i+1),labels.getValue(key),r.optString("source",key),SelectionValue(0,r.optDouble("value",-r.optInt("position",i+1).toDouble()),0,.8),r.optString("context","same"),
            if(required==null) emptyList() else strings(required).map { labels[it] ?: (it to it) },r.optBoolean("resolved",true)) }
    for(pool in listOf(items,items.reversed())) {
        val result=runCatching { EvidenceSelection.select(pool,case.optInt("chunk_cap",4),1200,1536) { keys ->
            val cost=case.optJSONObject("costs")?.optJSONArray(keys.joinToString(","));if(cost==null) keys.size*100 to keys.size*100+100 else cost.getInt(0) to cost.getInt(1) } }
        if(case.has("error"))assertEquals(case.getString("id"),case.getString("error"),(result.exceptionOrNull() as SelectionFailure).state)
        else {
            val plan=result.getOrThrow();assertEquals(case.getString("id"),strings(case.getJSONArray("selected")),plan.keys)
            val reasons=case.optJSONObject("reasons");if(reasons!=null)for(key in reasons.keys())assertEquals(reasons.getString(key),plan.decisions.single { it.key==key }.reason)
        }
    }
}
