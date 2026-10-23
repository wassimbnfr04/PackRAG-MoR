package org.packrag.product

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.file.Files
import java.util.UUID
import java.util.zip.ZipFile
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.packrag.crypto.RawManifestVerifier as Crypto
import org.packrag.model.*
import org.packrag.packs.*

/** Actual signed/SQLite registry contracts under both APKs, with explicit isolated test trust. */
@RunWith(AndroidJUnit4::class)
class SourceDetailsDeviceTest {
    private val instrument get()=InstrumentationRegistry.getInstrumentation()
    private val context get()=instrument.targetContext
    private val assets get()=instrument.context.assets
    private fun ref()=assets.open("source-details-corpus/signed-row-expectations.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
    private fun nullable(row:JSONObject,key:String):String?=if(row.isNull(key)) null else row.getString(key)
    private fun nullableLong(row:JSONObject,key:String):Long?=if(row.isNull(key)) null else row.getLong(key)
    private fun root()=File(context.filesDir,"source-details-${UUID.randomUUID()}").also { assertTrue(it.mkdirs()) }
    private fun registry(root:File,key:String):PackRegistry {
        val public=assets.open(key).use { it.readBytes() }
        val lock=context.assets.open("toolchain.lock.json").bufferedReader().use { JSONObject(it.readText()) }
        val schema=context.assets.open("schema.sql").bufferedReader().use { it.readText() }
        return PackRegistry(File(root,"registry"),PackVerifier(listOf(public),lock.getJSONObject("embedder").getJSONObject("pack_profile"),schema,true))
    }
    private fun input(root:File,row:JSONObject):File=File(root,"input.kpack").also { file ->
        assets.open(row.getString("asset")).use { source -> file.outputStream().use { source.copyTo(it) } }
        assertEquals(row.getString("pack_sha256"),Crypto.fileHash(file))
        assertEquals(row.getString("public_key_sha256"),Crypto.sha256(assets.open(row.getString("public_key_asset")).use { it.readBytes() }))
    }
    private fun identity(pack:ActivePack)=PackIdentity(pack.id,pack.version,pack.manifestHash)
    private fun state(registry:PackRegistry):List<Any> = listOf(registry.installed(),registry.snapshot().map(::identity),
        registry.installed().map { it.packId to registry.newestVersion(it.packId) },registry.installed().map { it.packId to registry.previousVersion(it.packId) })
    private fun attribution(expected:JSONObject,actual:SourceAttribution) {
        assertEquals(nullable(expected,"canonical_uri"),actual.canonicalUri);assertEquals(expected.getString("retrieved_at"),actual.retrievedAt)
        assertEquals(expected.getString("license"),actual.license);assertEquals(expected.getInt("redistribution_allowed")==1,actual.redistributionAllowed)
        assertEquals(expected.getString("source_type"),actual.sourceType);assertEquals(nullable(expected,"snapshot_path"),actual.snapshotPath);assertEquals(nullable(expected,"notes"),actual.notes)
    }
    private fun details(expected:JSONObject,actual:PackDetails,input:File) {
        assertEquals(PackIdentity(expected.getString("pack_id"),expected.getString("version"),expected.getString("manifest_sha256")),actual.identity)
        val rows=expected.getJSONArray("sources");assertEquals(rows.length(),actual.sources.size)
        for(i in 0 until rows.length()) {
            val row=rows.getJSONObject(i);val source=actual.sources[i]
            assertEquals(row.getString("source_id"),source.sourceId);assertEquals(row.getString("title"),source.title)
            assertEquals(row.getString("publisher"),source.publisher);assertEquals(row.getString("language"),source.language)
            assertEquals(row.getString("sha256_original"),source.originalSha256);attribution(row,source.attribution)
            assertEquals(nullable(row,"effective_from"),source.sourceFrom);assertEquals(nullable(row,"effective_until_excl"),source.sourceUntilExcl)
            assertEquals(nullable(row,"jurisdiction"),source.jurisdiction);assertEquals(nullable(row,"legal_status"),source.legalStatus)
            assertEquals(nullableLong(row,"authority_rank")?.toInt(),source.authorityRank)
            assertEquals(nullable(row,"document_version"),source.documentVersion);assertEquals(nullable(row,"issued_at"),source.issuedAt)
        }
        ZipFile(input).use { archive ->
            val raw=archive.getInputStream(archive.getEntry("manifest.json")).use { it.readBytes() };val manifest=JSONObject(raw.toString(Charsets.UTF_8))
            assertEquals(raw.size.toLong(),actual.manifestBytes);assertEquals(input.length(),actual.transportBytes)
            val files=manifest.getJSONArray("files");assertEquals((0 until files.length()).sumOf { files.getJSONObject(it).getLong("bytes") },actual.payloadBytes)
            assertEquals(manifest.getString("name"),actual.name);assertEquals(manifest.getString("domain"),actual.domain)
            assertEquals(manifest.getString("release_timestamp"),actual.releaseTimestamp)
            assertEquals(manifest.getJSONObject("publisher").getString("key_id"),actual.publisherKeyId)
            assertEquals(manifest.getJSONObject("publisher").getString("name"),actual.publisherName)
            assertEquals(manifest.getJSONObject("freshness").getString("update_check_after"),actual.updateCheckAfter)
            assertEquals(manifest.getJSONObject("counts").getInt("chunks"),actual.chunkCount)
            assertEquals(manifest.getJSONObject("embedding_profile").toString(),JSONObject(actual.embeddingProfileJson).toString())
            assertEquals(manifest.getJSONObject("build").toString(),JSONObject(actual.buildJson).toString())
            assertEquals(manifest.getJSONObject("calibration").toString(),JSONObject(actual.calibrationJson).toString())
            assertEquals(manifest.getJSONObject("calibration").getString("status"),actual.calibrationStatus)
            for((name,values) in listOf("languages" to actual.languages,"jurisdictions" to actual.jurisdictions)) {
                val a=manifest.getJSONArray(name);assertEquals((0 until a.length()).map { a.getString(it) },values)
            }
        }
    }
    private fun remove(root:File) { require(root.canonicalPath.startsWith(context.filesDir.canonicalPath+File.separator));assertTrue(root.deleteRecursively()) }
    private fun actualSources(details:PackDetails)=JSONArray().also { array -> details.sources.forEach { source ->
        val attribution=source.attribution
        array.put(JSONObject().put("source_id",source.sourceId).put("title",source.title).put("publisher",source.publisher)
            .put("language",source.language).put("sha256_original",source.originalSha256)
            .put("canonical_uri",attribution.canonicalUri ?: JSONObject.NULL).put("retrieved_at",attribution.retrievedAt ?: JSONObject.NULL)
            .put("license",attribution.license ?: JSONObject.NULL).put("redistribution_allowed",attribution.redistributionAllowed ?: JSONObject.NULL)
            .put("source_type",attribution.sourceType ?: JSONObject.NULL).put("snapshot_path",attribution.snapshotPath ?: JSONObject.NULL).put("notes",attribution.notes ?: JSONObject.NULL)
            .put("effective_from",source.sourceFrom ?: JSONObject.NULL).put("effective_until_excl",source.sourceUntilExcl ?: JSONObject.NULL)
            .put("jurisdiction",source.jurisdiction ?: JSONObject.NULL).put("legal_status",source.legalStatus ?: JSONObject.NULL)
            .put("authority_rank",source.authorityRank ?: JSONObject.NULL).put("document_version",source.documentVersion ?: JSONObject.NULL).put("issued_at",source.issuedAt ?: JSONObject.NULL))
    } }
    @Test fun originalSignedRowsActiveInactiveInspectionAndOwnedCopies() {
        val rows=ref().getJSONArray("packs");assertEquals(17,rows.length());val results=JSONArray()
        for(i in 0 until rows.length()) {
            val expected=rows.getJSONObject(i);val root=root();lateinit var saved:PackDetails
            try {
                val archive=input(root,expected)
                registry(root,expected.getString("public_key_asset")).use { registry ->
                    val pack=registry.activate(archive);val identity=identity(pack)
                    val expectedSources=expected.getJSONArray("sources");val bySource=(0 until expectedSources.length()).associate { expectedSources.getJSONObject(it).getString("source_id") to expectedSources.getJSONObject(it) }
                    val expectedChunks=expected.getJSONArray("chunks");val byChunk=(0 until expectedChunks.length()).associate { expectedChunks.getJSONObject(it).getString("chunk_id") to expectedChunks.getJSONObject(it) }
                    for(chunk in pack.chunks) {
                        attribution(bySource.getValue(chunk.sourceId),requireNotNull(chunk.attribution))
                        val original=byChunk.getValue(chunk.id);val location=requireNotNull(chunk.location)
                        assertEquals(nullable(original,"title"),location.chunkTitle);assertEquals(nullable(original,"section"),location.section)
                        assertEquals(nullableLong(original,"page_start"),location.pageStart);assertEquals(nullableLong(original,"page_end"),location.pageEnd)
                        assertEquals(nullableLong(original,"character_start"),location.characterStart);assertEquals(nullableLong(original,"character_end"),location.characterEnd)
                        assertEquals(original.getString("canonical_text"),chunk.canonicalText);assertEquals(original.getString("text_sha256"),chunk.textSha256)
                    }
                    for(active in listOf(true,false)) {
                        if(!active) registry.deactivate(pack.id)
                        val before=state(registry);val beforeHash=Crypto.fileHash(File(root,"registry/registry.sqlite"))
                        saved=registry.inspect(identity.packId,identity.version,identity.manifestSha256);details(expected,saved,archive)
                        assertEquals(before,state(registry));assertEquals(beforeHash,Crypto.fileHash(File(root,"registry/registry.sqlite")))
                        assertTrue(File(root,"registry/.staging").listFiles()!!.isEmpty())
                    }
                    assertThrows(UnsupportedOperationException::class.java) { (saved.sources as MutableList).clear() }
                    if(i==rows.length()-1) { assertEquals(11,saved.sources.size);assertEquals(10,saved.chunkCount);assertFalse(saved.sources.single { it.sourceId=="dev-unused" }.attribution.redistributionAllowed!!) }
                }
                details(expected,saved,archive) // Reader and registry are closed; values must remain usable.
                results.put(JSONObject().put("asset",expected.getString("asset")).put("manifest_sha256",saved.identity.manifestSha256)
                    .put("sources",saved.sources.size).put("actual_sources",actualSources(saved)).put("active_and_inactive_inspection",true).put("passed",true))
            } finally { remove(root) }
        }
        File(context.filesDir,"m4-source-details-rows.json").writeText(JSONObject().put("status","PASS").put("cases",results)
            .put("expectations_sha256",Crypto.sha256(assets.open("source-details-corpus/signed-row-expectations.json").use { it.readBytes() }))
            .put("test_trust","Explicit isolated fixture keys/development schema, separate from compiled app admission policy")
            .put("raw_reasoning_persisted",false).toString(2),Charsets.UTF_8)
    }
    @Test fun installedTamperIdentityMissingAndRemovedDetailsFailWithoutMutation() {
        val expected=ref().getJSONArray("packs").getJSONObject(16);val root=root();val cases=JSONArray()
        try {
            val archive=input(root,expected)
            registry(root,expected.getString("public_key_asset")).use { registry ->
                val pack=registry.activate(archive);val identity=identity(pack)
                fun reject(id:String,operation:()->Unit) {
                    val before=state(registry);val hash=Crypto.fileHash(File(root,"registry/registry.sqlite"))
                    val failure=runCatching(operation).exceptionOrNull();assertNotNull("Expected failure: $id",failure);assertTrue("Not a catastrophic error: $id",failure is Exception)
                    assertEquals(before,state(registry));assertEquals(hash,Crypto.fileHash(File(root,"registry/registry.sqlite")))
                    assertTrue(File(root,"registry/.staging").listFiles()!!.isEmpty())
                    cases.put(JSONObject().put("id",id).put("error_type",failure!!.javaClass.simpleName).put("passed",true))
                }
                for(name in listOf("knowledge.sqlite","dense.kdx","manifest.json","manifest.sig","transport.kpack","sources/thermal.txt")) {
                    val file=File(pack.root,name);val original=file.readBytes();val altered=original.copyOf();altered[0]=(altered[0].toInt() xor 1).toByte();file.writeBytes(altered)
                    try { reject("tampered-$name") { registry.inspect(identity.packId,identity.version,identity.manifestSha256) } } finally { file.writeBytes(original) }
                }
                val unexpected=File(pack.root,"unexpected.bin");unexpected.writeText("extra")
                try { reject("unexpected-installed-file") { registry.inspect(identity.packId,identity.version,identity.manifestSha256) } } finally { assertTrue(unexpected.delete()) }
                val originalFile=File(pack.root,"sources/thermal.txt");val original=originalFile.readBytes();val target=File(root,"symlink-target.txt");target.writeBytes(original);assertTrue(originalFile.delete())
                Files.createSymbolicLink(originalFile.toPath(),target.toPath())
                try { reject("installed-symbolic-link-even-with-correct-payload-bytes") { registry.inspect(identity.packId,identity.version,identity.manifestSha256) } }
                finally { Files.delete(originalFile.toPath());originalFile.writeBytes(original);assertTrue(target.delete()) }
                reject("wrong-requested-identity") { registry.inspect(identity.packId,identity.version,"0".repeat(64)) }
                reject("missing-version") { registry.inspect(identity.packId,"99.0.0",identity.manifestSha256) }
                registry.remove(identity.packId,identity.version)
                reject("removed-version") { registry.inspect(identity.packId,identity.version,identity.manifestSha256) }
            }
        } finally { remove(root) }
        File(context.filesDir,"m4-source-details-rejections.json").writeText(JSONObject().put("status","PASS").put("cases",cases)
            .put("active_trust_history_unchanged_during_inspection",true).put("raw_reasoning_persisted",false).toString(2),Charsets.UTF_8)
    }
}
