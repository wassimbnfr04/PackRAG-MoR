package org.packrag.product

import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.io.RandomAccessFile
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier
import org.packrag.packs.RegistryProcessLoss

@RunWith(AndroidJUnit4::class)
class AtomicRegistryDeviceTest {
    @Test fun atomicUpdateProcessLossOriginalCorruptionMigrationAndSnapshotIsolation() {
        val instrument=InstrumentationRegistry.getInstrumentation(); val context=instrument.targetContext; val assets=instrument.context.assets
        val corpus=assets.open("lifecycle-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val key=assets.open("lifecycle-corpus/public-key.raw").use { it.readBytes() }; assertEquals(corpus.getString("public_key_sha256"),Crypto.sha256(key))
        val profile=assets.open("parity-reference.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()).getJSONObject("lock").getJSONObject("embedder").getJSONObject("pack_profile") }
        val schema=assets.open("schema.sql").bufferedReader(Charsets.UTF_8).use { it.readText() }; val verifier=PackVerifier(listOf(key),profile,schema,true)
        val root=File(context.filesDir,"m3-atomic-${UUID.randomUUID()}"); assertTrue(root.mkdirs()); val inputs=mutableMapOf<String,File>(); val identities=mutableMapOf<String,String>(); val results=JSONArray()
        try {
            val cases=corpus.getJSONArray("cases")
            for(i in 0 until cases.length()) {
                val case=cases.getJSONObject(i); val file=File(root,case.getString("filename"))
                assets.open("lifecycle-corpus/"+file.name).use { source -> file.outputStream().use { source.copyTo(it) } }
                assertEquals(case.getString("sha256"),Crypto.fileHash(file)); inputs[case.getString("id")]=file; identities[case.getString("id")]=case.getString("manifest_sha256")
            }
            val id="org.packrag.development.walking-skeleton"
            val points=listOf("after_verify","after_fsync","after_rename","after_version_insert","after_active_write","before_commit","after_commit")
            for(point in points) {
                val registryRoot=File(root,"loss-$point"); var dbHash=""; var denseHash=""
                PackRegistry(registryRoot,verifier).use { registry ->
                    val pack=registry.activate(inputs.getValue("v1")); assertEquals("packs/$id/1.0.0",registry.installed().single().path)
                    dbHash=Crypto.fileHash(File(pack.root,"knowledge.sqlite")); denseHash=Crypto.fileHash(File(pack.root,"dense.kdx"))
                }
                val failing=PackRegistry(registryRoot,verifier) { current -> if(current==point) throw RegistryProcessLoss(current) }
                assertThrows(RegistryProcessLoss::class.java) { failing.activate(inputs.getValue("v2")) }; failing.close(); failing.close()
                PackRegistry(registryRoot,verifier).use { recovered ->
                    val committed=point=="after_commit"; val expected=if(committed) "v2" else "v1"; val pack=recovered.snapshot().single()
                    assertEquals(identities.getValue(expected),pack.manifestHash); assertEquals(if(committed) "1.0.1" else "1.0.0",pack.version)
                    assertFalse(pack.sparse("\"Aster\"").isEmpty()); assertEquals(dbHash,Crypto.fileHash(File(registryRoot,"packs/$id/1.0.0/knowledge.sqlite")))
                    assertEquals(denseHash,Crypto.fileHash(File(registryRoot,"packs/$id/1.0.0/dense.kdx")))
                    assertEquals(if(committed) 2 else 1,recovered.installed().size); assertEquals(if(committed) "1.0.0" else null,recovered.previousVersion(id))
                    assertEquals(0,File(registryRoot,".staging").listFiles()!!.size)
                    assertEquals(committed,File(registryRoot,"packs/$id/1.0.1").exists()); assertTrue(recovered.verificationFailures().isEmpty())
                    results.put(JSONObject().put("id","loss-$point").put("passed",true).put("expected_active",pack.version).put("actual_manifest_sha256",pack.manifestHash).put("old_payloads_unchanged",true))
                }
            }
            val ordinary=File(root,"ordinary")
            PackRegistry(ordinary,verifier).use { registry ->
                registry.activate(inputs.getValue("v1")); val pack=registry.activate(inputs.getValue("v2")); assertEquals(identities.getValue("v2"),pack.manifestHash)
                for(name in listOf("v2","collision","older","equal-build")) assertThrows(IllegalArgumentException::class.java) { registry.activate(inputs.getValue(name)) }
                assertEquals("1.0.1",registry.snapshot().single().version); assertEquals(2,registry.installed().size); assertEquals(0,File(ordinary,".staging").listFiles()!!.size)
                assertThrows(Exception::class.java) { PackRegistry(ordinary,verifier) }; assertEquals("1.0.1",registry.snapshot().single().version)
                results.put(JSONObject().put("id","immutable-identity-semver-and-exclusive-owner").put("passed",true))
            }
            for(payload in listOf("knowledge.sqlite","dense.kdx","manifest.json","manifest.sig","transport.kpack","unexpected.txt")) {
                val registryRoot=File(root,"corrupt-${payload.replace('.','-')}"); var oldDbHash=""
                PackRegistry(registryRoot,verifier).use { registry ->
                    val old=registry.activate(inputs.getValue("v1")); oldDbHash=Crypto.fileHash(File(old.root,"knowledge.sqlite"))
                    val current=registry.activate(inputs.getValue("v2")); val file=File(current.root,payload)
                    if(payload=="unexpected.txt") file.writeText("Synthetic unexpected installed file")
                    else RandomAccessFile(file,"rw").use { input -> val end=input.length()-1; input.seek(end); val byte=input.read(); input.seek(end); input.write(byte xor 1) }
                }
                PackRegistry(registryRoot,verifier).use { recovered ->
                    assertTrue("Corruption silently fell back: $payload",recovered.snapshot().isEmpty()); assertEquals(1,recovered.verificationFailures().size)
                    assertEquals("UNTRUSTED",recovered.installed().single { it.version=="1.0.1" }.trustState)
                    assertEquals("1.0.0",recovered.previousVersion(id)); assertEquals(oldDbHash,Crypto.fileHash(File(registryRoot,"packs/$id/1.0.0/knowledge.sqlite")))
                    results.put(JSONObject().put("id","installed-corruption-$payload").put("passed",true).put("automatic_rollback",false).put("reason",recovered.verificationFailures().single().reason))
                }
                PackRegistry(registryRoot,verifier).use { assertTrue(it.snapshot().isEmpty()) }
            }
            for(orphan in listOf(false,true)) {
                val registryRoot=File(root,"legacy-$orphan"); assertTrue(registryRoot.mkdirs()); val legacy=File(registryRoot,"stage-prototype")
                verifier.stage(inputs.getValue("v1"),legacy); val dbHash=Crypto.fileHash(File(legacy,"knowledge.sqlite"))
                if(orphan) verifier.stage(inputs.getValue("v1"),File(registryRoot,"packs/$id/1.0.0"))
                BundledSQLiteDriver().open(File(registryRoot,"registry.sqlite").absolutePath).use { db ->
                    db.prepare("CREATE TABLE active(pack_id TEXT PRIMARY KEY,version TEXT NOT NULL,manifest_hash TEXT NOT NULL,path TEXT NOT NULL)").use { it.step() }
                    db.prepare("INSERT INTO active VALUES(?,?,?,?)").use { query -> listOf(id,"1.0.0",identities.getValue("v1"),legacy.name).forEachIndexed { index,value -> query.bindText(index+1,value) }; query.step() }
                }
                if(!orphan) {
                    assertThrows(IllegalStateException::class.java) { PackRegistry(registryRoot,verifier) { point -> if(point=="migration_after_rename") error("Synthetic migration I/O failure") } }
                    assertTrue("Migration failure removed old source",legacy.exists()); assertEquals(dbHash,Crypto.fileHash(File(legacy,"knowledge.sqlite")))
                    BundledSQLiteDriver().open(File(registryRoot,"registry.sqlite").absolutePath).use { db -> db.prepare("SELECT path FROM active").use { query -> assertTrue(query.step()); assertEquals(legacy.name,query.getText(0)) } }
                }
                PackRegistry(registryRoot,verifier).use { migrated ->
                    val pack=migrated.snapshot().single(); assertEquals(identities.getValue("v1"),pack.manifestHash); assertEquals(dbHash,Crypto.fileHash(File(pack.root,"knowledge.sqlite")))
                    assertEquals("packs/$id/1.0.0",migrated.installed().single().path); assertFalse(legacy.exists()); assertFalse(pack.sparse("\"Aster\"").isEmpty())
                    results.put(JSONObject().put("id","legacy-migration-orphan-$orphan").put("passed",true).put("semantic_identity_unchanged",true))
                }
            }
            val emptyCase=assets.open("empty-corpus/case.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
            val emptyKey=assets.open("empty-corpus/public-key.raw").use { it.readBytes() }; assertEquals(emptyCase.getString("public_key_sha256"),Crypto.sha256(emptyKey))
            val emptyInput=File(root,"empty.kpack"); assets.open("empty-corpus/empty.kpack").use { source -> emptyInput.outputStream().use { source.copyTo(it) } }
            assertEquals(emptyCase.getString("sha256"),Crypto.fileHash(emptyInput)); val emptyVerifier=PackVerifier(listOf(emptyKey),profile,schema,true); val emptyRoot=File(root,"empty-registry")
            PackRegistry(emptyRoot,emptyVerifier).use { registry -> val pack=registry.activate(emptyInput); assertTrue(pack.chunks.isEmpty()); assertTrue(pack.sparse("\"Aster\"").isEmpty()); assertEquals(emptyCase.getString("manifest_sha256"),pack.manifestHash) }
            PackRegistry(emptyRoot,emptyVerifier).use { registry -> assertTrue(registry.snapshot().single().chunks.isEmpty()); assertTrue(registry.snapshot().single().sparse("\"Aster\"").isEmpty()) }
            assertEquals(emptyCase.getString("sha256"),Crypto.fileHash(emptyInput)); results.put(JSONObject().put("id","valid-zero-row-db-kdx-install-and-reopen").put("passed",true).put("fixture",emptyCase))
            val concurrent=File(root,"snapshot")
            PackRegistry(concurrent,verifier).use { registry ->
                registry.activate(inputs.getValue("v1")); val pool=Executors.newFixedThreadPool(2); val entered=CountDownLatch(1); val release=CountDownLatch(1); val writerEntered=CountDownLatch(1)
                try {
                    val reader=pool.submit<String> { registry.withSnapshot { packs -> entered.countDown(); assertTrue(release.await(30,TimeUnit.SECONDS)); assertEquals("1.0.0",packs.single().version); assertFalse(packs.single().sparse("\"Aster\"").isEmpty()); packs.single().manifestHash } }
                    assertTrue(entered.await(30,TimeUnit.SECONDS))
                    val writer=pool.submit<String> { writerEntered.countDown(); registry.activate(inputs.getValue("v2")).version }; assertTrue(writerEntered.await(30,TimeUnit.SECONDS))
                    assertThrows(TimeoutException::class.java) { writer.get(100,TimeUnit.MILLISECONDS) }; release.countDown()
                    assertEquals(identities.getValue("v1"),reader.get(30,TimeUnit.SECONDS)); assertEquals("1.0.1",writer.get(30,TimeUnit.SECONDS)); assertEquals("1.0.1",registry.snapshot().single().version)
                    results.put(JSONObject().put("id","query-snapshot-blocks-update").put("passed",true))
                } finally { release.countDown(); pool.shutdownNow(); assertTrue(pool.awaitTermination(30,TimeUnit.SECONDS)) }
            }
            for(i in 0 until cases.length()) { val case=cases.getJSONObject(i); assertEquals("Lifecycle mutated input",case.getString("sha256"),Crypto.fileHash(inputs.getValue(case.getString("id")))) }
            File(context.filesDir,"m3-atomic-registry.json").writeText(JSONObject().put("status","PASS").put("cases",results).put("corpus",corpus)
                .put("purpose","ACTUAL_ANDROID_FSYNC_RENAME_SQLITE_FAULT_RECOVERY_AND_INSTALLED_BYTES_GATE")
                .put("limits","Simulated process loss at explicit completed operations; not physical power interruption. Synthetic packs, no release calibration or performance acceptance.").toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator)); root.deleteRecursively() }
    }
}
