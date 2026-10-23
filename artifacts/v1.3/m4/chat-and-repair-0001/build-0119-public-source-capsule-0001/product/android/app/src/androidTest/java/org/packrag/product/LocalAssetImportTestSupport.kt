package org.packrag.product

import android.app.Application
import android.content.Context
import android.net.Uri
import android.os.ParcelFileDescriptor
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.Path
import java.nio.file.SimpleFileVisitor
import java.nio.file.FileVisitResult
import java.nio.file.attribute.BasicFileAttributes
import org.json.JSONObject
import org.junit.Assert.*
import org.packrag.crypto.RawManifestVerifier as Crypto

/** Test-only application isolation; production paths/permissions/configuration are unchanged. */
internal class AssetImportPrivateApplication(base:Context,private val root:File):Application() {
    init{attachBaseContext(base)}
    override fun getFilesDir()=root
    override fun getCacheDir()=File(root,"cache").also{check(it.mkdirs() || it.isDirectory)}
}
internal object LocalAssetImportTestSupport {
    val instrument get()=InstrumentationRegistry.getInstrumentation()
    val context get()=instrument.targetContext
    fun ownerGuard():Map<String,String> {
        val expected=instrument.context.assets.open("asset-import-source/owner-public-baseline.json").bufferedReader().use{JSONObject(it.readText())}
        assertEquals(50,expected.length());val observed=sortedMapOf<String,String>()
        for(name in expected.keys()) {
            val pieces=name.split('/');assertFalse(pieces.any{it in setOf(".private","..",".") || it.contains("keystore",true) || it.contains("seed",true)})
            assertTrue(name.startsWith("models/") || name.startsWith("packs/") || name.startsWith("production-registry/"))
            var path=context.filesDir.toPath();pieces.forEachIndexed { index,piece ->
                path=path.resolve(piece);val attrs=Files.readAttributes(path,BasicFileAttributes::class.java,LinkOption.NOFOLLOW_LINKS)
                assertFalse(attrs.isSymbolicLink);if(index<pieces.lastIndex)assertTrue(attrs.isDirectory) else assertTrue(attrs.isRegularFile)
            }
            observed[name]=Crypto.fileHash(path.toFile());assertEquals(name,expected.getString(name),observed[name])
        };return observed
    }
    fun grant(action:String):String {
        require(action in setOf("GRANT_CASES","GRANT_FULL_ASSETS"))
        val descriptor=instrument.uiAutomation.executeShellCommand("am broadcast --user 0 -n org.packrag.product.test/org.packrag.product.AssetFixtureGrantReceiver -a org.packrag.product.test.$action")
        return ParcelFileDescriptor.AutoCloseInputStream(descriptor).bufferedReader().use{it.readText()}.also{assertTrue(it.contains("result=1"))}
    }
    fun provider():JSONObject=context.contentResolver.query(Uri.parse("content://org.packrag.product.test.asset-fixtures/template-valid"),null,null,null,null)!!.use { cursor ->
        assertTrue(cursor.moveToFirst());JSONObject().apply{for(name in listOf("opens","closes","close_errors","provider_uid","opening_attempts","opening_cancelled","pipe_opens","pipe_writers_closed"))put(name,cursor.getInt(cursor.getColumnIndexOrThrow(name)))}
    }
    fun documentPickerPackage():String {
        val descriptor=instrument.uiAutomation.executeShellCommand("cmd package resolve-activity --brief -a android.intent.action.OPEN_DOCUMENT -c android.intent.category.OPENABLE -t application/octet-stream")
        val output=ParcelFileDescriptor.AutoCloseInputStream(descriptor).bufferedReader().use{it.readText()}
        val component=output.lineSequence().map{it.trim()}.single{it.matches(Regex("[A-Za-z0-9_.]+/[A-Za-z0-9_.$]+"))}
        return component.substringBefore('/')
    }
    fun deleteOwned(root:File,prefix:String) {
        require(root.parentFile!!.canonicalFile==context.filesDir.canonicalFile && root.name.matches(Regex("${Regex.escape(prefix)}[0-9a-f-]{36}")))
        val attrs=Files.readAttributes(root.toPath(),BasicFileAttributes::class.java,LinkOption.NOFOLLOW_LINKS);check(attrs.isDirectory && !attrs.isSymbolicLink)
        Files.walkFileTree(root.toPath(),object:SimpleFileVisitor<Path>(){
            override fun preVisitDirectory(dir:Path,attributes:BasicFileAttributes):FileVisitResult{check(dir.fileName.toString()!=".private");return FileVisitResult.CONTINUE}
            override fun visitFile(file:Path,attributes:BasicFileAttributes):FileVisitResult{Files.delete(file);return FileVisitResult.CONTINUE}
            override fun postVisitDirectory(dir:Path,error:java.io.IOException?):FileVisitResult{if(error!=null)throw error;Files.delete(dir);return FileVisitResult.CONTINUE}
        })
    }
}
