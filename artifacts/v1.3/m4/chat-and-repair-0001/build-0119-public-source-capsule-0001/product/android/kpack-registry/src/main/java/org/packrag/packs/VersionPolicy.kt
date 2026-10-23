package org.packrag.packs

/** Immutable identity and SemVer precedence; lifecycle UI adds deliberate rollback later. */
object VersionPolicy {
    fun newInstall(version: String, alreadyInstalled: Boolean, newest: String?) {
        val candidate = PackVersion.parse(version)
        require(!alreadyInstalled) { "Version already installed; replacement of immutable version forbidden" }
        require(newest == null || candidate > PackVersion.parse(newest)) { "Older/equal-precedence content requires deliberate activation with warning" }
    }
    fun needsWarning(version: String,newest: String?): Boolean = newest != null && PackVersion.parse(version) <= PackVersion.parse(newest)
    fun requireAcknowledgment(version: String,newest: String?,acknowledged: Boolean) {
        require(!needsWarning(version,newest) || acknowledged) { "Older/equal-precedence content requires deliberate activation with warning" }
    }
}
