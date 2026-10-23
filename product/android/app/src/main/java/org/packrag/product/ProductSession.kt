package org.packrag.product

import android.content.Context
import android.net.Uri
import java.io.Closeable
import java.io.File
import org.json.JSONObject
import org.packrag.embedding.GraniteEncoder
import org.packrag.generator.LlamaGenerator
import org.packrag.generator.GeneratorBackend
import org.packrag.generator.GenerationPolicy
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
class ProductSession(context: Context, registryRoot: File, keys: List<ByteArray>, developerMode: Boolean,
    private val generationPolicy:GenerationPolicy=GenerationPolicy.BASELINE,
    private val executionObserver:(String)->Unit = {}) : Closeable {
    private val files = context.filesDir
    private val resolver=context.contentResolver
    private val modelRoot=File(files,"models")
    private val lock = context.assets.open("toolchain.lock.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
    private val schema = context.assets.open("schema.sql").bufferedReader(Charsets.UTF_8).use { it.readText() }
    private val assetVerifier=LocalAssetVerifier(File(files,"models"))
    private var assetStatuses=assetVerifier.unchecked()
    private val configuredAssets=lock.getJSONObject("generator").let {
        require(it.getString("artifact")=="LFM2.5-2.6B-QAD-Q4_0.gguf" && it.getString("sha256")==LlamaGenerator.MODEL_SHA
            && it.getString("chat_template_sha256")==LlamaGenerator.TEMPLATE_SHA && it.getString("llama_cpp_commit")==LlamaGenerator.COMMIT)
        ConfiguredAssets(it.getString("model_id"),it.getString("artifact"),"QAD-Q4_0 (configured hash-pinned artifact)",
            lock.getJSONObject("embedder").getJSONObject("pack_profile").toString())
    }
    init {
        val g=lock.getJSONObject("generator");val e=lock.getJSONObject("embedder").getJSONObject("asset_sha256")
        require(g.getLong("bytes")==LocalAssetSlot.GENERATOR.expectedBytes && g.getString("sha256")==LocalAssetSlot.GENERATOR.expectedSha256
            && g.getString("chat_template_sha256")==LocalAssetSlot.TEMPLATE.expectedSha256
            && e.getString("tokenizer.json")==LocalAssetSlot.TOKENIZER.expectedSha256
            && e.getString("onnx/model.onnx")==LocalAssetSlot.ENCODER.expectedSha256) { "LOCAL_ASSET_CONFIGURATION_INVALID" }
        BlockingIo.run { LocalAssetImporter(modelRoot,::syncLocalAssetDirectory).reconcileIfPresent() }
    }
    val registry = PackRegistry(registryRoot, PackVerifier(keys, lock.getJSONObject("embedder").getJSONObject("pack_profile"), schema, developerMode))
    private var encoder: GraniteEncoder? = null
    @Volatile private var generator: GeneratorBackend? = null
    @Volatile private var runtime: PackRag? = null
    private val cancellation = AtomicLong(0)
    private var modelReadLease:Closeable?=null
    @Volatile private var importingSource:LocalAssetUriSource?=null
    val generatorLoadAndVerificationMs: Double? get() = generator?.loadAndVerificationMs
    private fun observedSession()=SessionDiagnostics(configuredAssets,encoder!=null,generator?.identity,generator?.loadAndVerificationMs)
    // Optional boundary observation records no model data and replaces no implementation.
    private fun <T> io(label:String,action:()->T):T=BlockingIo.run { executionObserver(label);action() }
    @Synchronized fun localAssetStatuses():List<LocalAssetStatus> = assetStatuses.toList()
    @Synchronized fun verifyLocalAssets():List<LocalAssetStatus> {
        val ticket=cancellation.get()
        assetStatuses=assetVerifier.unchecked()
        assetStatuses=LocalAssetLeases.read(modelRoot.toPath()).use {
            BlockingIo.run { assetVerifier.verify { ticket!=cancellation.get() } }
        }
        if(assetStatuses.any { it.condition!=LocalAssetCondition.VERIFIED }) releaseModels()
        return assetStatuses.toList()
    }
    private fun releaseModels() {
        runtime=null
        try { generator?.close();generator=null;encoder?.close();encoder=null }
        finally { if(generator==null && encoder==null){modelReadLease?.close();modelReadLease=null} }
    }

    @Synchronized fun importLocalAsset(slot:LocalAssetSlot,uri:Uri,progress:(LocalAssetImportProgress)->Unit={}):LocalAssetImportResult {
        val ticket=cancellation.get()
        releaseModels();assetStatuses=assetVerifier.unchecked()
        val source=LocalAssetUriSource(resolver,uri);importingSource=source
        try {
            val result=BlockingIo.run {
                LocalAssetImporter(modelRoot,::syncLocalAssetDirectory).install(slot,source::open,{ticket!=cancellation.get()},progress)
            }
            assetStatuses=assetStatuses.map { if(it.spec.slot==slot) LocalAssetStatus(it.spec,LocalAssetCondition.VERIFIED,result.bytes,result.sha256,result.completedAt) else it }
            return result
        } finally { importingSource=null;runCatching {source.close()} }
    }

    @Synchronized fun ask(query: Query): RuntimeTrace {
        val start = System.nanoTime()
        val ticket = cancellation.get()
        if (registry.snapshot().isEmpty()) return RuntimeTrace(Answer("NO_ACTIVE_PACK"), emptyList(), totalMs = (System.nanoTime() - start) / 1e6,session=observedSession())
        var initialization = 0.0
        if (runtime == null) {
            modelReadLease=LocalAssetLeases.read(modelRoot.toPath())
            try {
            try { verifyLocalAssets() }
            catch(cancel:LocalAssetCheckCancelled) {
                return RuntimeTrace(Answer("CANCELLED"),emptyList(),totalMs=(System.nanoTime()-start)/1e6,
                    initializationMs=(System.nanoTime()-start)/1e6,session=observedSession())
            }
            if(ticket!=cancellation.get()) return RuntimeTrace(Answer("CANCELLED"),emptyList(),totalMs=(System.nanoTime()-start)/1e6,
                initializationMs=(System.nanoTime()-start)/1e6,session=observedSession())
            if(assetStatuses.any { it.condition!=LocalAssetCondition.VERIFIED }) throw LocalAssetsUnavailable(assetStatuses.toList())
            val hashes = lock.getJSONObject("embedder").getJSONObject("asset_sha256")
            if (encoder == null) encoder = io("ENCODER_CONSTRUCTOR") { GraniteEncoder(File(files, "models/granite"), hashes.getString("tokenizer.json"), hashes.getString("onnx/model.onnx")) }
            if (generator == null) generator = io("GENERATOR_CONSTRUCTOR") { LlamaGenerator(File(files, "models/LFM2.5-2.6B-QAD-Q4_0.gguf"), File(files, "models/chat_template.jinja"),generationPolicy=generationPolicy) }
            runtime = PackRag(registry, encoder!!, generator!!) { pack,terms -> io("SQLITE_SPARSE") { pack.sparse(terms) } }
            initialization = (System.nanoTime() - start) / 1e6
            } catch(failure:Exception){releaseModels();throw failure}
            finally { if(runtime==null && generator==null && encoder==null){modelReadLease?.close();modelReadLease=null} }
        }
        if (ticket != cancellation.get()) return RuntimeTrace(Answer("CANCELLED"), emptyList(), totalMs = (System.nanoTime() - start) / 1e6, initializationMs = initialization,session=observedSession())
        val observed=observedSession()
        executionObserver("RUNTIME_CPU")
        return runtime!!.ask(query) { ticket != cancellation.get() }.copy(totalMs = (System.nanoTime() - start) / 1e6, initializationMs = initialization,session=observed)
    }
    fun cancel() { cancellation.incrementAndGet(); importingSource?.abort();runtime?.cancel() ?: generator?.cancel() }
    @Synchronized override fun close() {
        releaseModels();registry.close()
    }
}
