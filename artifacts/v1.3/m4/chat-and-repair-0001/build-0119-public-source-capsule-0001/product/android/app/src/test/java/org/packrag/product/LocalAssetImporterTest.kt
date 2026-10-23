package org.packrag.product

import java.io.ByteArrayInputStream
import java.io.File
import java.io.IOException
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.Path
import java.nio.file.SimpleFileVisitor
import java.nio.file.FileVisitResult
import java.nio.file.attribute.BasicFileAttributes
import java.util.concurrent.atomic.AtomicBoolean
import org.junit.Assert.*
import org.junit.Test

/** Independent known bytes/pin; assert conservation of the old final file on failure. */
class LocalAssetImporterTest {
    private val hello="hello".toByteArray()
    private val sha="2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    private fun fixture(action:(File,File,LocalAssetImporter)->Unit) {
        val base=Files.createTempDirectory("packrag-import-test-").toAbsolutePath().normalize()
        val root=base.resolve("models").toFile();assertTrue(root.mkdir())
        val final=File(root,LocalAssetSlot.TEMPLATE.relativePath);final.writeText("older")
        try {action(root,final,LocalAssetImporter(root,{},listOf(LocalAssetSpec(LocalAssetSlot.TEMPLATE,5,sha))))}
        finally {
            require(base.parent==Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize())
            require(base.fileName.toString().startsWith("packrag-import-test-"))
            Files.walkFileTree(base,object:SimpleFileVisitor<Path>() {
                override fun visitFile(file:Path,attrs:BasicFileAttributes):FileVisitResult {Files.delete(file);return FileVisitResult.CONTINUE}
                override fun postVisitDirectory(dir:Path,error:IOException?):FileVisitResult {if(error!=null) throw error;Files.delete(dir);return FileVisitResult.CONTINUE}
            })
        }
    }
    private fun unchanged(root:File,final:File) {assertEquals("older",final.readText());assertFalse(File(root,".asset-import-v1").exists())}
    @Test fun realStagedReadbackReplacesOnlyFixedFinalAndClosesOneSource()=fixture { root,final,importer ->
        val other=File(root,"legacy.partial");other.writeText("leave alone")
        var opens=0;var closes=0;val events=mutableListOf<LocalAssetImportProgress>()
        val result=importer.install(LocalAssetSlot.TEMPLATE,{
            opens++;object:ByteArrayInputStream(hello){override fun close(){closes++;super.close()}}
        },progress={events.add(it)})
        assertEquals(1,opens);assertEquals(1,closes);assertArrayEquals(hello,final.readBytes())
        assertEquals(5L,result.bytes);assertEquals(sha,result.sha256);assertTrue(result.directorySynced);assertTrue(result.stagingCleaned)
        assertEquals(LocalAssetImportStage.COMMITTED,events.last().stage);assertEquals(5L,events.last().copiedBytes)
        assertEquals("leave alone",other.readText());assertFalse(File(root,".asset-import-v1").exists())
    }
    @Test fun emptyTruncatedOversizedAndCorruptPreserveOldBytes()=fixture { root,final,importer ->
        for(bytes in listOf(byteArrayOf(),byteArrayOf(1,2),ByteArray(6),"world".toByteArray())) {
            val failure=assertThrows(LocalAssetImportFailed::class.java){importer.install(LocalAssetSlot.TEMPLATE,{ByteArrayInputStream(bytes)})}
            assertEquals(if(bytes.size==5) "LOCAL_ASSET_IMPORT_HASH_MISMATCH" else "LOCAL_ASSET_IMPORT_WRONG_SIZE",failure.code)
            unchanged(root,final)
        }
    }
    @Test fun shortAndZeroReadsObserveEveryByteWithoutReopening()=fixture { _,final,importer ->
        var opens=0
        importer.install(LocalAssetSlot.TEMPLATE,{
            opens++;object:ByteArrayInputStream(hello) {
                var zero=true
                override fun read(bytes:ByteArray,offset:Int,length:Int):Int {
                    if(zero){zero=false;return 0};return super.read(bytes,offset,minOf(length,2))
                }
            }
        })
        assertEquals(1,opens);assertArrayEquals(hello,final.readBytes())
    }
    @Test fun cancellationBeforeOpenDuringCopyAndBeforeRenamePreservesOldBytes()=fixture { root,final,importer ->
        assertThrows(LocalAssetImportCancelled::class.java){importer.install(LocalAssetSlot.TEMPLATE,{throw AssertionError("must not open")},{true})}
        unchanged(root,final)
        for(phase in listOf(LocalAssetImportStage.COPYING,LocalAssetImportStage.VERIFYING,LocalAssetImportStage.COMMITTING)) {
            val cancel=AtomicBoolean(false)
            assertThrows(LocalAssetImportCancelled::class.java) {
                importer.install(LocalAssetSlot.TEMPLATE,{ByteArrayInputStream(hello)},{cancel.get()}) {
                    if(it.stage==phase && (phase!=LocalAssetImportStage.COPYING || it.copiedBytes>0)) cancel.set(true)
                }
            }
            unchanged(root,final)
        }
    }
    @Test fun sourceReadAndPrecommitDirectorySyncFailureAreSafeAndSanitized()=fixture { root,final,importer ->
        val failure=assertThrows(LocalAssetImportFailed::class.java){importer.install(LocalAssetSlot.TEMPLATE,{throw IOException("private provider detail")})}
        assertEquals("LOCAL_ASSET_IMPORT_IO",failure.code);assertFalse(failure.message!!.contains("provider detail"));unchanged(root,final)
        val failedSync=LocalAssetImporter(root,{throw IOException("sync unavailable")},listOf(LocalAssetSpec(LocalAssetSlot.TEMPLATE,5,sha)))
        assertThrows(LocalAssetImportFailed::class.java){failedSync.install(LocalAssetSlot.TEMPLATE,{throw AssertionError("must not open")})}
        unchanged(root,final)
    }
    @Test fun lateCancellationAndPostcommitSyncFailureReportInstalledBytes()=fixture { root,final,_ ->
        val cancel=AtomicBoolean(false)
        val importer=LocalAssetImporter(root,{if(it==root.toPath().toAbsolutePath() && final.readText()=="hello") throw IOException("final directory sync")},listOf(LocalAssetSpec(LocalAssetSlot.TEMPLATE,5,sha)))
        val result=importer.install(LocalAssetSlot.TEMPLATE,{ByteArrayInputStream(hello)},{cancel.get()}) {
            if(it.stage==LocalAssetImportStage.COMMITTED) cancel.set(true)
        }
        assertArrayEquals(hello,final.readBytes());assertEquals(sha,result.sha256);assertFalse(result.directorySynced);assertFalse(result.stagingCleaned)
    }
    @Test fun readersAndWritersExcludeReplacementBeforeInputAndReleaseIdempotently()=fixture { root,final,importer ->
        val a=LocalAssetLeases.read(root.toPath());val b=LocalAssetLeases.read(root.toPath().resolve("."))
        assertThrows(LocalAssetsBusy::class.java){importer.install(LocalAssetSlot.TEMPLATE,{throw AssertionError("must not open")})}
        unchanged(root,final);a.close();a.close()
        assertThrows(LocalAssetsBusy::class.java){LocalAssetLeases.write(root.toPath())};b.close()
        LocalAssetLeases.write(root.toPath()).use {assertThrows(LocalAssetsBusy::class.java){LocalAssetLeases.read(root.toPath())}}
        importer.install(LocalAssetSlot.TEMPLATE,{ByteArrayInputStream(hello)});assertArrayEquals(hello,final.readBytes())
    }
    @Test fun unknownStagingEntriesArePreservedAndNoInputIsOpened()=fixture { root,final,importer ->
        val stage=File(root,".asset-import-v1");assertTrue(stage.mkdir())
        File(stage,"owner.marker").writeText("PackRAG owned asset import v1\n")
        val unknown=File(stage,"not-owned");unknown.writeText("keep")
        assertThrows(LocalAssetImportFailed::class.java){importer.install(LocalAssetSlot.TEMPLATE,{throw AssertionError("must not open")})}
        assertEquals("older",final.readText());assertEquals("keep",unknown.readText());assertTrue(File(stage,"owner.marker").exists())
    }
    @Test fun startupRemovesOnlyValidatedOwnedStagesAndLeavesLegacyPartials()=fixture { root,final,importer ->
        val stage=File(root,".asset-import-v1");assertTrue(stage.mkdir())
        File(stage,"owner.marker").writeText("PackRAG owned asset import v1\n")
        File(stage,"TEMPLATE-00000000-0000-0000-0000-000000000000.part").writeText("he")
        val legacy=File(root,"chat_template.jinja.part");legacy.writeText("legacy")
        assertEquals(1,importer.reconcileIfPresent());assertFalse(stage.exists())
        assertEquals("legacy",legacy.readText());assertEquals("older",final.readText());assertEquals(0,importer.reconcileIfPresent())
    }
    @Test fun corruptMarkerAndOversizedOwnedStageCannotBeDeletedOrPromoted()=fixture { root,final,importer ->
        val stage=File(root,".asset-import-v1");assertTrue(stage.mkdir())
        val marker=File(stage,"owner.marker");marker.writeText("PackRAG owned asset import v0\n")
        assertThrows(LocalAssetImportFailed::class.java){importer.reconcileIfPresent()};assertEquals("older",final.readText())
        marker.writeText("PackRAG owned asset import v1\n")
        val large=File(stage,"TEMPLATE-00000000-0000-0000-0000-000000000000.part");large.writeText("too big")
        val error=assertThrows(LocalAssetImportFailed::class.java){importer.install(LocalAssetSlot.TEMPLATE,{throw AssertionError("must not open")})}
        assertTrue(error.cleanupPending);assertEquals("too big",large.readText());assertTrue(marker.exists());assertEquals("older",final.readText())
    }
    @Test fun stageChangedAfterCopyIsCaughtByIndependentReadbackBeforeCommit()=fixture { root,final,importer ->
        val error=assertThrows(LocalAssetImportFailed::class.java){
            importer.install(LocalAssetSlot.TEMPLATE,{ByteArrayInputStream(hello)},progress={event->
                if(event.stage==LocalAssetImportStage.VERIFYING) {
                    Files.newDirectoryStream(File(root,".asset-import-v1").toPath(),"*.part").use{stream->stream.forEach{Files.write(it,"world".toByteArray())}}
                }
            })
        }
        assertEquals("LOCAL_ASSET_IMPORT_HASH_MISMATCH",error.code);assertFalse(error.cleanupPending);unchanged(root,final)
    }
}
