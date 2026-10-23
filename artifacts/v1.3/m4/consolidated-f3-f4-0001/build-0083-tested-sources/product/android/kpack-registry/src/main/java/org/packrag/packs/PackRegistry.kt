package org.packrag.packs

import androidx.sqlite.SQLiteConnection
import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import java.io.Closeable
import java.io.File
import java.io.RandomAccessFile
import java.nio.channels.FileLock
import java.nio.file.Files
import java.util.UUID
import org.json.JSONObject
import org.packrag.model.PackDetails
import org.packrag.model.PackIdentity
import org.packrag.model.PackOverview
import org.packrag.crypto.RawManifestVerifier as Crypto

/** Only test fault callbacks throw this; simulated loss skips normal file cleanup. */
class RegistryProcessLoss(val point: String) : Error("Simulated registry process loss: $point")
data class PackVerificationFailure(val packId: String, val version: String, val reason: String)
data class InstalledVersion(val packId: String, val version: String, val manifestHash: String, val path: String, val trustState: String)
class OlderContentRequired(val packId: String,val version: String,val manifestHash: String,val newestVersion: String) : IllegalArgumentException("Older or equal-precedence content requires acknowledgment")

/** Immutable installed versions, atomic active switch and fail-closed reopening. */
class PackRegistry(private val root: File, private val verifier: PackVerifier,
                   private val testCachePages: Int? = null,
                   private val fault: (String) -> Unit = {}) : Closeable {
    private val lease = acquire(root)
    private lateinit var database: SQLiteConnection
    private val active = sortedMapOf<String, ActivePack>()
    private val failures = mutableListOf<PackVerificationFailure>()
    private var closed = false
    private var inTransaction = false
    private val staging = File(root,".staging")
    private val packs = File(root,"packs")
    init {
        try {
            require(staging.exists() || staging.mkdirs()); require(packs.exists() || packs.mkdirs())
            database = BundledSQLiteDriver().open(File(root,"registry.sqlite").absolutePath)
            execute(database,"PRAGMA journal_mode=DELETE"); execute(database,"PRAGMA synchronous=FULL"); execute(database,"PRAGMA trusted_schema=OFF")
            // Only the separate-process crash probe uses this to force dirty
            // page spill and a genuinely hot journal before SIGKILL.
            testCachePages?.let { require(it in 1..32); execute(database,"PRAGMA cache_size=$it"); execute(database,"PRAGMA cache_spill=ON") }
            execute(database,"CREATE TABLE IF NOT EXISTS active(pack_id TEXT PRIMARY KEY,version TEXT NOT NULL,manifest_hash TEXT NOT NULL,path TEXT NOT NULL)")
            execute(database,"CREATE TABLE IF NOT EXISTS versions(pack_id TEXT NOT NULL,version TEXT NOT NULL,manifest_hash TEXT NOT NULL,path TEXT NOT NULL,trust_state TEXT NOT NULL,PRIMARY KEY(pack_id,version))")
            execute(database,"CREATE TABLE IF NOT EXISTS previous(pack_id TEXT PRIMARY KEY,version TEXT NOT NULL)")
            execute(database,"CREATE TABLE IF NOT EXISTS newest(pack_id TEXT PRIMARY KEY,version TEXT NOT NULL)")
            execute(database,"CREATE TABLE IF NOT EXISTS identities(pack_id TEXT NOT NULL,version TEXT NOT NULL,manifest_hash TEXT NOT NULL,PRIMARY KEY(pack_id,version))")
            execute(database,"CREATE TABLE IF NOT EXISTS last_active(pack_id TEXT PRIMARY KEY,version TEXT NOT NULL)")
            if(testCachePages != null) execute(database,"CREATE TABLE IF NOT EXISTS crash_probe(payload BLOB NOT NULL)")
            transaction {
                for(record in installed()) {
                    val known = rowsBound("SELECT manifest_hash FROM identities WHERE pack_id=? AND version=?",record.packId,record.version).singleOrNull()?.single()
                    require(known == null || known == record.manifestHash) { "Stored version identity mismatch" }
                    statement("INSERT OR IGNORE INTO identities VALUES(?,?,?)",record.packId,record.version,record.manifestHash)
                }
            }
            DurableFiles.directory(root)
            cleanupOrphans()
            for(record in rows(database,"SELECT pack_id,version,manifest_hash,path FROM active ORDER BY pack_id")) {
                val id = record[0]!!; val version = record[1]!!; val hash = record[2]!!
                val original = owned(record[3]!!)
                val manifest = try { verifyInstalled(original,id,version,hash) }
                catch(error: Exception) {
                    failures.add(PackVerificationFailure(id,version,error.message?.take(256) ?: error.javaClass.name))
                    transaction {
                        statement("DELETE FROM active WHERE pack_id=?",id)
                        statement("UPDATE versions SET trust_state='UNTRUSTED' WHERE pack_id=? AND version=?",id,version)
                    }
                    continue
                }
                    val target = location(id,version)
                    // Migrate the M2 prototype only after validating all original bytes.
                    if(original.canonicalFile != target.canonicalFile) {
                        require(!target.exists()) { "Migration destination already exists" }
                        val stage = File(staging,"migration-${UUID.randomUUID()}")
                        verifier.stage(File(original,"transport.kpack"),stage)
                        DurableFiles.tree(stage); target.parentFile!!.mkdirs(); DurableFiles.directory(packs); DurableFiles.rename(stage,target); fault("migration_after_rename")
                        transaction {
                            putVersion(id,version,hash,relative(target),"VERIFIED")
                            putActive(id,version,hash,relative(target)); rememberNewest(id,version)
                        }
                        deleteOwned(original)
                    } else transaction {
                        val existing = versionRecord(id,version)
                        require(existing == null || (existing.manifestHash == hash && existing.path == relative(target))) { "Registry version identity mismatch" }
                        putVersion(id,version,hash,relative(target),"VERIFIED"); rememberNewest(id,version)
                        statement("INSERT OR REPLACE INTO last_active VALUES(?,?)",id,version)
                    }
                    active[id] = ActivePack(target,manifest)
            }
            // A renamed but uncommitted version is never activated on recovery.
            cleanupOrphans()
        } catch(error: Throwable) { close(); throw error }
    }

    @Synchronized fun activate(archive: File, acknowledgeOlder: Boolean = false, observer:(PackImportEvent)->Unit={}): ActivePack {
        val observation=PackImportObservation(observer);var registryStarted=false
        open(); val stage = File(staging,"install-${UUID.randomUUID()}")
        var accepted: ActivePack? = null; var target: File? = null; var committed = false
        try {
            val manifest = verifier.stage(archive,stage,observer); fault("after_verify")
            registryStarted=true;observation.emit(PackImportEvent(PackImportStage.REGISTRY_COMMIT,PackImportState.STARTED))
            val id = manifest.getString("pack_id"); val version = manifest.getString("version"); val hash = Crypto.fileHash(File(stage,"manifest.json"))
            val highest = rowsBound("SELECT version FROM newest WHERE pack_id=?",id).singleOrNull()?.single()
            require(versionRecord(id,version) == null) { "Version already installed; replacement of immutable version forbidden" }
            val knownHash = rowsBound("SELECT manifest_hash FROM identities WHERE pack_id=? AND version=?",id,version).singleOrNull()?.single()
            require(knownHash == null || knownHash == hash) { "Previously seen version has different authenticated content" }
            // Reinstalling the exact newest identity is not an older-content
            // activation; an equal-precedence different build still warns.
            val exactNewestReinstall = highest == version && knownHash == hash
            if(!exactNewestReinstall && VersionPolicy.needsWarning(version,highest) && !acknowledgeOlder) throw OlderContentRequired(id,version,hash,highest!!)
            val destination = location(id,version); require(!destination.exists()) { "Unregistered version path exists; reopen registry to recover" }
            DurableFiles.tree(stage); fault("after_fsync")
            require(destination.parentFile!!.exists() || destination.parentFile!!.mkdirs()); DurableFiles.directory(packs)
            DurableFiles.rename(stage,destination); target = destination; fault("after_rename")
            accepted = ActivePack(destination,manifest)
            transaction {
                putVersion(id,version,hash,relative(destination),"VERIFIED"); fault("after_version_insert")
                rememberPrevious(id,version)
                putActive(id,version,hash,relative(destination)); rememberNewest(id,version); fault("after_active_write")
                fault("before_commit")
            }
            committed = true;observation.emit(PackImportEvent(PackImportStage.REGISTRY_COMMIT,PackImportState.COMMITTED)); fault("after_commit"); DurableFiles.directory(root)
            active.remove(id)?.close(); active[id] = accepted
            observation.emit(PackImportEvent(PackImportStage.REGISTRY_COMMIT,PackImportState.PASSED))
            return accepted
        } catch(loss: RegistryProcessLoss) {
            accepted?.close(); close(); throw loss
        } catch(error: Throwable) {
            if(registryStarted) observation.emit(PackImportEvent(PackImportStage.REGISTRY_COMMIT,
                if(error is OlderContentRequired) PackImportState.AWAITING_CONSENT
                else if(committed || target!=null) PackImportState.RECOVERY_REQUIRED else PackImportState.REJECTED))
            accepted?.close()
            if(committed) close() else {
                if(stage.exists()) deleteOwned(stage)
                // A COMMIT I/O error can be ambiguous. Keep renamed bytes until
                // the next authenticated recovery rather than deleting a
                // possibly committed active version.
                if(target != null) close()
            }
            if(error is Exception && error !is OlderContentRequired && error !is PackImportRejected)
                throw PackImportRejected(if(committed || target!=null) PackImportFailure.REGISTRY_RECOVERY_REQUIRED
                    else PackImportFailure.REGISTRY_CHANGE_REJECTED,error)
            throw error
        }
    }

    /** Holds the registry monitor throughout retrieval/generation; mutations wait. */
    @Synchronized fun <T> withSnapshot(block: (List<ActivePack>) -> T): T { open(); return block(active.values.toList()) }
    @Synchronized fun snapshot(): List<ActivePack> { open(); return active.values.toList() }
    @Synchronized fun installed(): List<InstalledVersion> { open(); return rows(database,"SELECT pack_id,version,manifest_hash,path,trust_state FROM versions ORDER BY pack_id,version").map { InstalledVersion(it[0]!!,it[1]!!,it[2]!!,it[3]!!,it[4]!!) } }
    @Synchronized fun verificationFailures(): List<PackVerificationFailure> { open(); return failures.toList() }
    /** Reverify even inactive versions, without changing active/trust/history state. */
    @Synchronized fun overview(id:String,version:String,expectedManifestHash:String):PackOverview {
        open();val record=versionRecord(id,version) ?: error("Version is not installed")
        require(record.manifestHash==expectedManifestHash) { "Requested installed identity mismatch" }
        return withVerifiedInstalled(owned(record.path),id,version,record.manifestHash) { checked,manifest ->
            readPackOverview(checked,manifest,PackIdentity(id,version,record.manifestHash))
        }
    }
    /** Reverify even inactive versions, without changing active/trust/history state. */
    @Synchronized fun inspect(id:String,version:String,expectedManifestHash:String):PackDetails {
        open();val record=versionRecord(id,version) ?: error("Version is not installed")
        require(record.manifestHash==expectedManifestHash) { "Requested installed identity mismatch" }
        return withVerifiedInstalled(owned(record.path),id,version,record.manifestHash) { checked,manifest ->
            readPackDetails(checked,manifest,PackIdentity(id,version,record.manifestHash))
        }
    }
    @Synchronized fun previousVersion(id: String): String? { open(); return rowsBound("SELECT version FROM previous WHERE pack_id=?",id).singleOrNull()?.single() }

    @Synchronized fun newestVersion(id: String): String? { open(); return rowsBound("SELECT version FROM newest WHERE pack_id=?",id).singleOrNull()?.single() }
    @Synchronized fun deactivate(id: String) {
        open(); require(id in active) { "Pack is not active" }
        var committed = false
        try {
            transaction { statement("DELETE FROM active WHERE pack_id=?",id); fault("deactivate_before_commit") }
            committed = true; fault("deactivate_after_commit"); active.remove(id)!!.close()
        } catch(error: Throwable) { if(committed || error is RegistryProcessLoss) close(); throw error }
    }
    @Synchronized fun activateInstalled(id: String,version: String,acknowledgeOlder: Boolean = false): ActivePack {
        open(); val record = versionRecord(id,version) ?: error("Version is not installed")
        require(active[id]?.version != version) { "Version is already active" }
        val highest = newestVersion(id)
        if(highest != version && VersionPolicy.needsWarning(version,highest) && !acknowledgeOlder) throw OlderContentRequired(id,version,record.manifestHash,highest!!)
        val original = owned(record.path)
        val manifest = try { verifyInstalled(original,id,version,record.manifestHash) }
        catch(error: Exception) {
            transaction { statement("UPDATE versions SET trust_state='UNTRUSTED' WHERE pack_id=? AND version=?",id,version) }
            throw error
        }
        val accepted = ActivePack(original,manifest); var committed = false
        try {
            transaction {
                rememberPrevious(id,version)
                putVersion(id,version,record.manifestHash,record.path,"VERIFIED"); putActive(id,version,record.manifestHash,record.path)
                fault("reactivate_before_commit")
            }
            committed = true; fault("reactivate_after_commit"); active.remove(id)?.close(); active[id] = accepted
            return accepted
        } catch(error: Throwable) { accepted.close(); if(committed || error is RegistryProcessLoss) close(); throw error }
    }
    @Synchronized fun rollback(id: String,acknowledgeOlder: Boolean): ActivePack {
        open(); val previous = previousVersion(id) ?: error("No previous version is retained")
        require(acknowledgeOlder) { "Deliberate rollback requires older-content acknowledgment" }
        return activateInstalled(id,previous,true)
    }
    @Synchronized fun remove(id: String,version: String) {
        open(); val record = versionRecord(id,version) ?: error("Version is not installed")
        val original = owned(record.path)
        var committed = false
        try {
            transaction {
                statement("DELETE FROM active WHERE pack_id=? AND version=?",id,version)
                statement("DELETE FROM previous WHERE pack_id=? AND version=?",id,version)
                statement("DELETE FROM versions WHERE pack_id=? AND version=?",id,version); fault("remove_before_commit")
                statement("DELETE FROM last_active WHERE pack_id=? AND version=?",id,version)
            }
            committed = true; fault("remove_after_commit"); if(active[id]?.version == version) active.remove(id)!!.close()
            if(original.exists()) deleteOwned(original); DurableFiles.directory(original.parentFile!!)
        } catch(error: Throwable) { if(committed || error is RegistryProcessLoss) close(); throw error }
        // identities/newest are deliberately retained as lightweight history.
    }

    /** Test mode only: dirty-page pressure within the transaction being killed. */
    @Synchronized fun forceProbePageSpill() {
        open(); require(testCachePages != null && inTransaction)
        repeat(16) { execute(database,"INSERT INTO crash_probe VALUES(zeroblob(65536))") }
    }

    private fun verifyInstalled(original:File,id:String,version:String,hash:String):JSONObject =
        withVerifiedInstalled(original,id,version,hash) { _,manifest -> manifest }
    private fun <T> withVerifiedInstalled(original: File,id: String,version: String,hash: String,block:(File,JSONObject)->T):T {
        val checked = File(staging,"verify-${UUID.randomUUID()}")
        try {
            val manifest = verifier.stage(File(original,"transport.kpack"),checked)
            require(manifest.getString("pack_id") == id && manifest.getString("version") == version && Crypto.fileHash(File(checked,"manifest.json")) == hash) { "Installed identity mismatch" }
            val expected = mutableSetOf("transport.kpack","manifest.json","manifest.sig")
            val declared = manifest.getJSONArray("files")
            for(index in 0 until declared.length()) {
                val file = declared.getJSONObject(index); val name = file.getString("path"); expected.add(name)
                val payload = File(original,name)
                require(!Files.isSymbolicLink(payload.toPath()) && payload.isFile && payload.length() == file.getLong("bytes") && Crypto.fileHash(payload) == file.getString("sha256")) { "Installed payload hash/length mismatch: $name" }
            }
            for(name in listOf("manifest.json","manifest.sig","transport.kpack")) require(Crypto.fileHash(File(original,name)) == Crypto.fileHash(File(checked,name))) { "Installed control/transport mismatch: $name" }
            Files.walk(original.toPath()).use { paths ->
                val files = paths.iterator().asSequence().toList()
                require(files.none { Files.isSymbolicLink(it) })
                require(files.filter { Files.isRegularFile(it) }.map { original.toPath().relativize(it).toString().replace(File.separatorChar,'/') }.toSet() == expected) { "Unexpected/missing installed file" }
            }
            return block(checked,manifest)
        } finally { if(checked.exists()) deleteOwned(checked) }
    }
    private fun location(id: String,version: String): File {
        require(Regex("[a-z0-9]+(?:[.-][a-z0-9]+)+").matches(id) && id.toByteArray().size <= 255)
        PackVersion.parse(version); require(version.toByteArray().size <= 255)
        return owned("packs/$id/$version")
    }
    private fun relative(file: File) = root.toPath().relativize(file.toPath()).toString().replace(File.separatorChar,'/')
    private fun owned(path: String): File = File(root,path).also { require(it.canonicalPath.startsWith(root.canonicalPath+File.separator)) }
    private fun deleteOwned(file: File) {
        require(file.canonicalPath.startsWith(root.canonicalPath+File.separator))
        require(file.deleteRecursively()) { "Could not clean owned pack directory" }
    }
    private fun cleanupOrphans() {
        staging.listFiles()?.forEach(::deleteOwned)
        val registered = (installed().map { owned(it.path).canonicalPath } + rows(database,"SELECT path FROM active").map { owned(it.single()!!).canonicalPath }).toSet()
        packs.listFiles()?.forEach { publisher -> publisher.listFiles()?.forEach { version -> if(version.canonicalPath !in registered) deleteOwned(version) } }
        DurableFiles.directory(staging); DurableFiles.directory(packs)
    }
    private fun open() { check(!closed) { "Registry is closed" } }
    private fun statement(sql: String,vararg values: String) { database.prepare(sql).use { query -> values.forEachIndexed { index,value -> query.bindText(index+1,value) }; query.step() } }
    private fun rowsBound(sql: String,vararg values: String): List<List<String?>> = database.prepare(sql).use { query ->
        values.forEachIndexed { index,value -> query.bindText(index+1,value) }
        buildList { while(query.step()) add((0 until query.getColumnCount()).map { if(query.isNull(it)) null else query.getText(it) }) }
    }
    private fun versionRecord(id: String,version: String): InstalledVersion? = rowsBound("SELECT pack_id,version,manifest_hash,path,trust_state FROM versions WHERE pack_id=? AND version=?",id,version).singleOrNull()?.let { InstalledVersion(it[0]!!,it[1]!!,it[2]!!,it[3]!!,it[4]!!) }
    private fun putVersion(id: String,version: String,hash: String,path: String,trust: String) {
        val known = rowsBound("SELECT manifest_hash FROM identities WHERE pack_id=? AND version=?",id,version).singleOrNull()?.single()
        require(known == null || known == hash) { "Previously seen version identity mismatch" }
        statement("INSERT OR IGNORE INTO identities VALUES(?,?,?)",id,version,hash)
        statement("INSERT OR REPLACE INTO versions VALUES(?,?,?,?,?)",id,version,hash,path,trust)
    }
    private fun putActive(id: String,version: String,hash: String,path: String) {
        statement("INSERT OR REPLACE INTO active VALUES(?,?,?,?)",id,version,hash,path)
        statement("INSERT OR REPLACE INTO last_active VALUES(?,?)",id,version)
    }
    private fun rememberPrevious(id: String,version: String) {
        val prior = active[id]?.version ?: rowsBound("SELECT version FROM last_active WHERE pack_id=?",id).singleOrNull()?.single() ?: previousVersion(id)
        if(prior != null && prior != version && versionRecord(id,prior) != null) statement("INSERT OR REPLACE INTO previous VALUES(?,?)",id,prior)
        else if(previousVersion(id) == version) statement("DELETE FROM previous WHERE pack_id=?",id)
    }
    private fun rememberNewest(id: String,version: String) {
        val prior = rowsBound("SELECT version FROM newest WHERE pack_id=?",id).singleOrNull()?.single()
        if(prior == null || PackVersion.parse(version) > PackVersion.parse(prior)) statement("INSERT OR REPLACE INTO newest VALUES(?,?)",id,version)
    }
    private fun transaction(block: () -> Unit) {
        execute(database,"BEGIN IMMEDIATE")
        inTransaction = true
        try { block(); execute(database,"COMMIT") }
        catch(error: Throwable) { runCatching { execute(database,"ROLLBACK") }; throw error }
        finally { inTransaction = false }
    }
    @Synchronized override fun close() {
        if(closed) return
        closed = true
        try { active.values.forEach { it.close() }; active.clear() }
        finally { try { if(::database.isInitialized) database.close() } finally { lease.second.release(); lease.first.close() } }
    }
    companion object {
        private fun acquire(root: File): Pair<RandomAccessFile,FileLock> {
            require(root.exists() || root.mkdirs())
            val file = RandomAccessFile(File(root,"registry.lock"),"rw")
            try { return file to (file.channel.tryLock() ?: error("Registry already open by another owner")) }
            catch(error: Throwable) { file.close(); throw error }
        }
    }
}
