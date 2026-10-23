package org.packrag.product

import org.packrag.packs.PackImportFailure
import org.packrag.packs.PackImportRejected

/** Only these fixed strings reach product error/status UI; never Throwable.message. */
fun safeOperationFailure(error:Throwable):String = when(error) {
    is PackImportRejected -> when(error.category) {
        PackImportFailure.DOCUMENT_READ_FAILED -> "DOCUMENT_READ_FAILED: The selected file could not be copied. Choose it again."
        PackImportFailure.SNAPSHOT_COPY_FAILED -> "SNAPSHOT_COPY_FAILED: The private verification copy could not be saved."
        PackImportFailure.ARCHIVE_REJECTED -> "ARCHIVE_REJECTED: The archive failed safety or format checks."
        PackImportFailure.SIGNATURE_OR_MANIFEST_REJECTED -> "SIGNATURE_OR_MANIFEST_REJECTED: Signature or signed-manifest checks failed."
        PackImportFailure.MANIFEST_PROFILE_REJECTED -> "MANIFEST_PROFILE_REJECTED: The signed manifest, profile or compatibility is invalid."
        PackImportFailure.POLICY_REJECTED -> "POLICY_REJECTED: Uncalibrated pack requires developer mode."
        PackImportFailure.PAYLOAD_REJECTED -> "PAYLOAD_REJECTED: Declared payload sizes, hashes or archive membership failed verification."
        PackImportFailure.DATABASE_INDEX_REJECTED -> "DATABASE_INDEX_REJECTED: Knowledge database or dense index validation failed."
        PackImportFailure.REGISTRY_CHANGE_REJECTED -> "REGISTRY_CHANGE_REJECTED: The pack change could not be completed. Check installed packs."
        PackImportFailure.REGISTRY_RECOVERY_REQUIRED -> "REGISTRY_RECOVERY_REQUIRED: A storage failure made completion uncertain. Review the rechecked installed state before retrying."
    }
    is LocalAssetsUnavailable -> "LOCAL_ASSETS_UNAVAILABLE: Check the pinned local files before asking again."
    else -> "OPERATION_FAILED: The operation could not be completed. Check local files and installed packs before retrying."
}

fun safeQueryInputCode(error:IllegalArgumentException):String = error.message?.takeIf {
    it in setOf("INVALID_QUERY_DATE","INVALID_QUERY_JURISDICTION","INVALID_QUERY_TEXT","EMPTY_QUESTION","QUERY_TOO_LONG")
} ?: "INVALID_QUERY"
