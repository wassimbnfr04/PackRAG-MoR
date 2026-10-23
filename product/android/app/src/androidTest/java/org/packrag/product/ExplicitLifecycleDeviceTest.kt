package org.packrag.product

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.io.RandomAccessFile
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.model.Query
import org.packrag.packs.PackRegistry
import org.packrag.packs.PackVerifier
import org.packrag.packs.OlderContentRequired
import org.packrag.packs.RegistryProcessLoss

@RunWith(AndroidJUnit4::class)
class ExplicitLifecycleDeviceTest {
    @Test fun explicitActivationRollbackRemovalIdentityHistoryAndCommittedRecovery() {
        val instrument=InstrumentationRegistry.getInstrumentation(); val context=instrument.targetContext; val assets=instrument.context.assets
        val corpus=assets.open("lifecycle-corpus/cases.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
        val key=assets.open("lifecycle-corpus/public-key.raw").use { it.readBytes() }; val emptyKey=assets.open("empty-corpus/public-key.raw").use { it.readBytes() }
        val profile=assets.open("parity-reference.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()).getJSONObject("lock").getJSONObject("embedder").getJSONObject("pack_profile") }
        val schema=assets.open("schema.sql").bufferedReader(Charsets.UTF_8).use { it.readText() }; val verifier=PackVerifier(listOf(key,emptyKey),profile,schema,true)
        val root=File(context.filesDir,"m3-explicit-${UUID.randomUUID()}"); assertTrue(root.mkdirs()); val inputs=mutableMapOf<String,File>(); val hashes=mutableMapOf<String,String>(); val results=JSONArray()
        val id="org.packrag.development.walking-skeleton"; val emptyId="org.packrag.development.empty"
        fun passed(name: String) { results.put(JSONObject().put("id",name).put("passed",true)); File(context.filesDir,"m3-explicit-progress.json").writeText(JSONObject().put("status","RUNNING").put("cases",results).toString(2),Charsets.UTF_8) }
        try {
            val cases=corpus.getJSONArray("cases")
            for(i in 0 until cases.length()) { val case=cases.getJSONObject(i); val file=File(root,case.getString("filename")); assets.open("lifecycle-corpus/"+file.name).use { source -> file.outputStream().use { source.copyTo(it) } }; assertEquals(case.getString("sha256"),Crypto.fileHash(file)); inputs[case.getString("id")]=file; hashes[case.getString("id")]=case.getString("manifest_sha256") }
            val empty=File(root,"empty.kpack"); assets.open("empty-corpus/empty.kpack").use { source -> empty.outputStream().use { source.copyTo(it) } }
            val registryRoot=File(root,"ordinary")
            PackRegistry(registryRoot,verifier).use { registry ->
                registry.activate(inputs.getValue("v1")); registry.activate(inputs.getValue("v2")); registry.activate(inputs.getValue("v3")); registry.activate(empty)
                assertEquals(setOf(id,emptyId),registry.snapshot().map { it.id }.toSet()); passed("multiple-installed-active-pack-identities")
                assertThrows(IllegalArgumentException::class.java) { registry.rollback(id,false) }
                assertEquals("1.0.10",registry.snapshot().single { it.id==id }.version)
                assertEquals(hashes.getValue("v2"),registry.rollback(id,true).manifestHash); assertEquals("1.0.10",registry.newestVersion(id)); assertEquals("1.0.10",registry.previousVersion(id)); passed("deliberate-rollback-keeps-newest-history")
                assertEquals("1.0.10",registry.activateInstalled(id,"1.0.10").version); registry.remove(id,"1.0.1")
                assertFalse(File(registryRoot,"packs/$id/1.0.1").exists())
                assertThrows(IllegalArgumentException::class.java) { registry.activate(inputs.getValue("collision"),true) }; assertEquals("1.0.10",registry.snapshot().single { it.id==id }.version); passed("removed-identity-cannot-be-relabelled")
                val warning=assertThrows(OlderContentRequired::class.java) { registry.activate(inputs.getValue("older")) }; assertEquals("0.9.0",warning.version); assertEquals("1.0.10",warning.newestVersion); assertEquals(hashes.getValue("older"),warning.manifestHash)
                assertEquals("0.9.0",registry.activate(inputs.getValue("older"),true).version); assertEquals("1.0.10",registry.newestVersion(id)); passed("older-import-requires-explicit-acknowledgment")
                registry.deactivate(id); assertEquals(listOf(emptyId),registry.snapshot().map { it.id })
                assertThrows(OlderContentRequired::class.java) { registry.activateInstalled(id,"0.9.0") }
                assertEquals("1.0.10",registry.activateInstalled(id,"1.0.10").version); passed("deactivate-and-explicit-reactivate")
                val stale=File(registryRoot,"packs/$id/1.0.0/knowledge.sqlite")
                RandomAccessFile(stale,"rw").use { file -> val at=file.length()-1; file.seek(at); val byte=file.read(); file.seek(at); file.write(byte xor 1) }
                assertThrows(Exception::class.java) { registry.activateInstalled(id,"1.0.0",true) }; assertEquals("1.0.10",registry.snapshot().single { it.id==id }.version)
                assertEquals("UNTRUSTED",registry.installed().single { it.packId==id && it.version=="1.0.0" }.trustState); passed("untrusted-inactive-version-does-not-displace-active")
                registry.remove(id,"1.0.0"); registry.remove(id,"1.0.10"); assertEquals(listOf(emptyId),registry.snapshot().map { it.id })
                assertEquals(hashes.getValue("v3"),registry.activate(inputs.getValue("v3")).manifestHash); passed("exact-newest-reinstall-preserves-immutable-identity")
                registry.deactivate(id); registry.deactivate(emptyId); assertTrue(registry.snapshot().isEmpty()); assertEquals("1.0.10",registry.newestVersion(id))
            }
            ProductSession(context,registryRoot,listOf(key,emptyKey),true).use { session ->
                val answer=session.ask(Query("Aster-9 temperature limit?","2026-10-05")); assertEquals("NO_ACTIVE_PACK",answer.answer.state); assertNull(session.generatorLoadAndVerificationMs); passed("all-deactivated-no-pack-without-weight-load")
            }
            PackRegistry(registryRoot,verifier).use { registry -> assertEquals("1.0.10",registry.activateInstalled(id,"1.0.10").version); assertEquals(1,registry.snapshot().size); passed("restart-retains-explicit-active-set") }
            val equalRoot=File(root,"equal")
            PackRegistry(equalRoot,verifier).use { registry -> registry.activate(inputs.getValue("v2")); assertThrows(OlderContentRequired::class.java) { registry.activate(inputs.getValue("equal-build")) }; assertEquals("1.0.1+build2",registry.activate(inputs.getValue("equal-build"),true).version); assertEquals("1.0.1",registry.newestVersion(id)); passed("equal-precedence-build-metadata-is-not-newer") }
            for(operation in listOf("deactivate","remove","reactivate")) for(after in listOf(false,true)) {
                val registry=File(root,"loss-$operation-$after"); val point=operation+if(after) "_after_commit" else "_before_commit"
                PackRegistry(registry,verifier).use { it.activate(inputs.getValue("v1")); it.activate(inputs.getValue("v2")) }
                val failing=PackRegistry(registry,verifier) { current -> if(current==point) throw RegistryProcessLoss(current) }
                assertThrows(RegistryProcessLoss::class.java) { when(operation) { "deactivate" -> failing.deactivate(id); "remove" -> failing.remove(id,"1.0.1"); else -> failing.activateInstalled(id,"1.0.0",true) } }; failing.close()
                PackRegistry(registry,verifier).use { recovered ->
                    val expected=if(!after) "1.0.1" else if(operation=="reactivate") "1.0.0" else null
                    assertEquals(expected,recovered.snapshot().singleOrNull()?.version)
                    assertEquals(!(after && operation=="remove"),File(registry,"packs/$id/1.0.1").exists())
                    assertTrue(File(registry,"packs/$id/1.0.0/knowledge.sqlite").exists()); assertEquals("1.0.1",recovered.newestVersion(id)); passed("committed-recovery-$point")
                }
            }
            for(i in 0 until cases.length()) { val case=cases.getJSONObject(i); assertEquals(case.getString("sha256"),Crypto.fileHash(inputs.getValue(case.getString("id")))) }
            File(context.filesDir,"m3-explicit-lifecycle.json").writeText(JSONObject().put("status","PASS").put("cases",results).put("corpus",corpus)
                .put("purpose","ACTUAL_ANDROID_EXPLICIT_LIFECYCLE_IDENTITIES_WARNINGS_AND_ATOMIC_RECOVERY")
                .put("limits","UI warning presentation is a separate gate. Six CRUD faults are controlled exception tests; actual process-death evidence is recorded separately under B.").toString(2),Charsets.UTF_8)
        } finally { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator)); root.deleteRecursively() }
    }
}
