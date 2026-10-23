package org.packrag.product

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import java.io.File
import java.time.LocalDate
import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.model.Answer
import org.packrag.model.PackIdentity
import org.packrag.model.PackDetails
import org.packrag.packs.OlderContentRequired
import org.packrag.runtime.RuntimeTrace

data class PackRow(val id: String, val version: String, val hash: String, val trust: String, val active: Boolean, val newest: String?, val previous: String?) {
    val tag: String get() = "$id@$version"
}
data class PackDecision(val kind: String, val id: String, val version: String, val newest: String? = null)
data class UiState(val busy: Boolean = false, val message: String = "No active knowledge pack.", val answer: Answer? = null,
                   val packs: List<String> = emptyList(), val installed: List<PackRow> = emptyList(), val decision: PackDecision? = null,
                   val submission: SubmittedQuery? = null, val trace: RuntimeTrace? = null,
                   val activeFreshness: List<PackFreshness> = emptyList(), val inputError: String? = null,
                   val detailRequest:PackIdentity?=null,val details:PackDetails?=null,val detailsError:String?=null,
                   val completedResultId:String?=null,val localAssets:List<LocalAssetStatus> = emptyList())

class PackRagViewModel(application: Application, private val registryRoot: File = ProductConfiguration.defaultRoot(application)) : AndroidViewModel(application) {
    private val mutable = MutableStateFlow(UiState())
    val state = mutable.asStateFlow()
    private val mutex = Mutex()
    @Volatile private var session: ProductSession? = null
    private var running: Job? = null
    private var epoch = 0L
    // Accessed only under mutex. Caller URIs are never reopened after consent.
    private var pending: PackDecision? = null
    private var pendingTransport: File? = null
    private var pendingTransportHash: String? = null

    private fun session(): ProductSession {
        if (session == null) {
            val app = getApplication<Application>()
            session = ProductSession(app, registryRoot, ProductConfiguration.keys(app), developerMode = BuildConfig.ALLOW_DEVELOPMENT_PACKS)
        }
        return session!!
    }
    private fun state(message: String? = null, answer: Answer? = null): UiState {
        val registry = session().registry
        val snapshot = registry.snapshot()
        val active = snapshot.associate { it.id to it.version }
        val rows = registry.installed().map { PackRow(it.packId, it.version, it.manifestHash, it.trustState,
            active[it.packId] == it.version, registry.newestVersion(it.packId), registry.previousVersion(it.packId)) }
        return UiState(message = message ?: if(active.isEmpty()) "No active knowledge pack." else ProductConfiguration.readyMessage(),
            answer = answer, packs = active.map { "${it.key}@${it.value}" }, installed = rows, decision = pending,
            activeFreshness = snapshot.map { PackFreshness(PackIdentity(it.id,it.version,it.manifestHash),it.manifest.getJSONObject("freshness").getString("update_check_after")) },
            localAssets=session().localAssetStatuses())
    }
    private fun clearPending() {
        pendingTransport?.let { check(!it.exists() || it.delete()) { "Could not delete private pending import" } }
        pending = null; pendingTransport = null; pendingTransportHash = null
    }
    init { launchAction("Verifying active packs…") { state() } }

    private fun launchAction(message: String, submission: SubmittedQuery? = null,preserveResult:Boolean=false,
        detailRequest:PackIdentity?=null, action: suspend () -> UiState) {
        val ticket = ++epoch
        val previous = running
        session?.cancel(); previous?.cancel()
        val priorState=mutable.value
        mutable.value = mutable.value.copy(busy = true, message = message,
            answer = if(preserveResult) priorState.answer else null, submission = if(preserveResult) priorState.submission else submission,
            trace = if(preserveResult) priorState.trace else null,inputError = if(preserveResult) priorState.inputError else null,
            completedResultId=if(preserveResult) priorState.completedResultId else null,
            detailRequest=detailRequest,details=null,detailsError=null)
        running = viewModelScope.launch {
            previous?.join()
            try {
                val result = withContext(Dispatchers.IO) { mutex.withLock { action() } }
                if (ticket == epoch) mutable.value = if(preserveResult) result.copy(answer=priorState.answer,submission=priorState.submission,
                    trace=priorState.trace,inputError=priorState.inputError,completedResultId=priorState.completedResultId) else result
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (failure: Exception) {
                val result = withContext(Dispatchers.IO) { mutex.withLock {
                    clearPending(); session?.close(); session = null
                    // Reopening resolves any ambiguous commit and refreshes trust labels.
                    runCatching { state(failure.message ?: "Operation failed", Answer("RUNTIME_ERROR")) }
                        .getOrElse { UiState(message = failure.message ?: "Operation failed", answer = Answer("RUNTIME_ERROR")) }
                } }
                // Recovery opens a fresh session. Retain the completed failed-file observation,
                // with its timestamp, instead of replacing it with that session's unchecked slots.
                val observedAssets=(failure as? LocalAssetsUnavailable)?.statuses
                if (ticket == epoch) mutable.value = result.copy(submission = submission,
                    localAssets=observedAssets?.toList() ?: result.localAssets)
            }
        }
    }
    fun inspectPack(id:String,version:String,hash:String) {
        val requested=PackIdentity(id,version,hash)
        launchAction("Reverifying installed pack details…",preserveResult=true,detailRequest=requested) {
            clearPending()
            try { val details=session().registry.inspect(id,version,hash)
                state("Installed content freshly verified.").copy(detailRequest=requested,details=details)
            } catch(failure:Exception) {
                state("PACK_DETAIL_VERIFICATION_FAILED").copy(detailRequest=requested,detailsError=failure.message?.take(256) ?: "Installed content could not be verified.")
            }
        }
    }
    fun closeDetails() { if(!mutable.value.busy) mutable.value=mutable.value.copy(detailRequest=null,details=null,detailsError=null) }
    fun checkLocalAssets() { launchAction("Checking pinned local files…",preserveResult=true) {
        clearPending();session().verifyLocalAssets();state("Local asset check completed.")
    } }
    fun ask(question: String, asOf: String = LocalDate.now().toString(), jurisdiction: String = "", currentLaw: Boolean = false) {
        val query = try { submittedQuery(question,asOf,jurisdiction,currentLaw) }
        catch(failure: IllegalArgumentException) {
            val code = failure.message ?: "INVALID_QUERY"
            launchAction("Checking form input…") { clearPending(); state("INVALID_QUERY",Answer("INVALID_QUERY")).copy(inputError = code) }
            return
        }
        // Capture form values synchronously. Authenticated manifests are copied under the action mutex.
        val submitted = SubmittedQuery(query,emptyList())
        launchAction("Checking evidence and generating…",submitted) {
            clearPending(); val current = session()
            val captured = SubmittedQuery(query,current.registry.snapshot().map {
                PackFreshness(PackIdentity(it.id,it.version,it.manifestHash),it.manifest.getJSONObject("freshness").getString("update_check_after"))
            })
            val trace = withContext(Dispatchers.Default) { current.ask(query) }
            trace.evidenceContext?.let { check(it.query == query && it.identities == captured.packs.map { pack -> pack.identity }) { "Captured evidence context changed" } }
            trace.diagnostics?.context?.let { check(it.query==query && it.identities==captured.packs.map { pack -> pack.identity }) { "Captured diagnostic context changed" } }
            state(trace.answer.state,trace.answer).copy(submission = captured,trace = trace,completedResultId=UUID.randomUUID().toString())
        }
    }
    fun importPack(uri: Uri) { launchAction("Verifying signed KPack…") {
        clearPending()
        val app = getApplication<Application>()
        val transport = File(app.cacheDir, "import-${UUID.randomUUID()}.kpack")
        try {
            requireNotNull(app.contentResolver.openInputStream(uri)).use { input -> transport.outputStream().use { output ->
                val buffer = ByteArray(65536); var size = 0L
                while (true) { val count = input.read(buffer); if (count < 0) break
                    size += count; require(size <= 513L * 1024 * 1024) { "KPack exceeds transport limit" }; output.write(buffer, 0, count) }
            } }
            try { session().registry.activate(transport); state() }
            catch (older: OlderContentRequired) {
                pending = PackDecision("IMPORT_OLDER", older.packId, older.version, older.newestVersion)
                pendingTransport = transport; pendingTransportHash = Crypto.fileHash(transport)
                state("Confirmation required.")
            }
        } finally { if(pendingTransport != transport) check(!transport.exists() || transport.delete()) }
    } }
    fun activate(id: String, version: String) { launchAction("Verifying installed version…") {
        clearPending()
        try { session().registry.activateInstalled(id, version); state() }
        catch (older: OlderContentRequired) { pending = PackDecision("ACTIVATE_OLDER", id, version, older.newestVersion); state("Confirmation required.") }
    } }
    fun rollback(id: String) { launchAction("Preparing deliberate rollback…") {
        clearPending(); val registry = session().registry
        val previous = requireNotNull(registry.previousVersion(id)) { "No previous version is retained" }
        pending = PackDecision("ROLLBACK", id, previous, registry.newestVersion(id)); state("Confirmation required.")
    } }
    fun deactivate(id: String) { launchAction("Deactivating pack…") { clearPending(); session().registry.deactivate(id); state() } }
    fun requestRemove(id: String, version: String) { launchAction("Preparing removal…") {
        clearPending(); pending = PackDecision("REMOVE", id, version); state("Confirmation required.")
    } }
    fun cancelDecision() { launchAction("Cancelling pack change…") { clearPending(); state() } }
    fun confirmDecision() { launchAction("Applying confirmed pack change…") {
        val decision = requireNotNull(pending) { "No pack change is pending" }
        try {
            val registry = session().registry
            when(decision.kind) {
                "IMPORT_OLDER" -> { val transport = requireNotNull(pendingTransport); require(Crypto.fileHash(transport) == pendingTransportHash) { "Pending import changed" }; registry.activate(transport, true) }
                "ACTIVATE_OLDER" -> registry.activateInstalled(decision.id, decision.version, true)
                "ROLLBACK" -> { require(registry.previousVersion(decision.id) == decision.version) { "Rollback target changed" }; registry.rollback(decision.id, true) }
                "REMOVE" -> registry.remove(decision.id, decision.version)
                else -> error("Unknown pack change")
            }
        } finally { clearPending() }
        state()
    } }
    fun cancel() {
        ++epoch; session?.cancel(); running?.cancel()
        mutable.value = mutable.value.copy(busy = false, message = "Cancelled.", answer = Answer("CANCELLED"), submission = null, trace = null, inputError = null,
            detailRequest=null,details=null,detailsError=null,completedResultId=null)
    }
    override fun onCleared() {
        session?.cancel()
        CoroutineScope(SupervisorJob() + Dispatchers.IO).launch { mutex.withLock { clearPending(); session?.close(); session = null } }
        super.onCleared()
    }
}
