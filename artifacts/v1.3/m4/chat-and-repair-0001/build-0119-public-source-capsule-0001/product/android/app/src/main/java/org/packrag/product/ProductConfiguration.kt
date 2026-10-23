package org.packrag.product

import android.content.Context
import android.content.Intent
import java.io.File
import java.util.UUID
import org.packrag.crypto.ApprovedPublishers
import org.packrag.crypto.RawManifestVerifier as Crypto

/** Build-owned policy; never derived from a pack, URI or launch extra. */
object ProductConfiguration {
    fun approvedKeys(context: Context): List<ByteArray> = context.assets.open("release-trust.json").use { ApprovedPublishers.keys(it.readBytes()) }
    fun keys(context: Context, allowDevelopment: Boolean = BuildConfig.ALLOW_DEVELOPMENT_PACKS): List<ByteArray> {
        require(!allowDevelopment || BuildConfig.DEBUG) { "Development trust requires a debug build" }
        val approved = approvedKeys(context)
        val keys = if(allowDevelopment) approved + listOf("development-public-key.raw","lifecycle-public-key.raw").map { name -> context.assets.open(name).use { it.readBytes() } } else approved
        require(keys.size in 1..8 && keys.all { it.size==32 } && keys.map(Crypto::keyId).distinct().size==keys.size) { "Invalid built-in trust configuration" }
        return keys
    }
    fun defaultRoot(context: Context) = File(context.filesDir,if(BuildConfig.ALLOW_DEVELOPMENT_PACKS) "packs" else "production-registry")
    fun launchRoot(context: Context,intent: Intent): File {
        // Production ignores debug-only routing, including malformed untrusted extras.
        if(!BuildConfig.ALLOW_DEVELOPMENT_PACKS) return defaultRoot(context)
        require(BuildConfig.DEBUG)
        val testId = intent.getStringExtra("packrag.debug.uiTestId") ?: return defaultRoot(context)
        require(UUID.fromString(testId).toString()==testId)
        return File(context.filesDir,"ui-tests/$testId").also { require(it.canonicalPath.startsWith(File(context.filesDir,"ui-tests").canonicalPath+File.separator)) }
    }
    fun readyMessage() = if(BuildConfig.ALLOW_DEVELOPMENT_PACKS) "Ready. Developer pack mode." else "Ready."
}
