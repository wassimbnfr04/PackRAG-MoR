package org.packrag.packs

/** Observed operations, in separate byte domains; never an estimated overall percentage. */
enum class PackImportStage {
    SELECTED_DOCUMENT_COPY, SNAPSHOT_COPY, ARCHIVE_AUDIT, SIGNATURE_AUTHENTICATION,
    MANIFEST_PROFILE_POLICY, PAYLOAD_INTEGRITY, DATABASE_INDEX, REGISTRY_COMMIT
}
enum class PackImportState { STARTED, PROGRESS, PASSED, REJECTED, AWAITING_CONSENT, COMMITTED, RECOVERY_REQUIRED }
enum class PackImportFailure {
    DOCUMENT_READ_FAILED, SNAPSHOT_COPY_FAILED, ARCHIVE_REJECTED, SIGNATURE_OR_MANIFEST_REJECTED,
    MANIFEST_PROFILE_REJECTED, POLICY_REJECTED, PAYLOAD_REJECTED, DATABASE_INDEX_REJECTED,
    REGISTRY_CHANGE_REJECTED, REGISTRY_RECOVERY_REQUIRED
}
data class PackImportEvent(val stage:PackImportStage,val state:PackImportState,
    val bytes:Long?=null,val totalBytes:Long?=null) {
    init { require(bytes==null || bytes>=0);require(totalBytes==null || totalBytes>=0)
        require(bytes==null || totalBytes==null || bytes<=totalBytes) }
}
class PackImportRejected(val category:PackImportFailure,cause:Throwable) :
    IllegalArgumentException(category.name,cause)
class PackPolicyRejected : IllegalArgumentException("Uncalibrated pack requires developer mode")

/** An optional presentation observer has no authority over verification or commit. */
class PackImportObservation(private val observer:(PackImportEvent)->Unit={}) {
    fun emit(event:PackImportEvent) { runCatching { observer(event) } }
    fun <T> checked(stage:PackImportStage,totalBytes:Long?=null,block:((Long)->Unit)->T):T {
        var copied=0L;var reported=-1L
        val countsBytes=stage in setOf(PackImportStage.SELECTED_DOCUMENT_COPY,PackImportStage.SNAPSHOT_COPY,PackImportStage.PAYLOAD_INTEGRITY)
        emit(PackImportEvent(stage,PackImportState.STARTED,if(countsBytes || totalBytes!=null) 0 else null,totalBytes))
        try {
            val value=block { observed ->
                require(observed>=copied);require(totalBytes==null || observed<=totalBytes)
                copied=observed
                if(reported<0 || observed-reported>=1024*1024) {
                    emit(PackImportEvent(stage,PackImportState.PROGRESS,observed,totalBytes));reported=observed
                }
            }
            emit(PackImportEvent(stage,PackImportState.PASSED,
                if(countsBytes || reported>=0 || totalBytes!=null) copied else null,totalBytes))
            return value
        } catch(error:Exception) {
            emit(PackImportEvent(stage,PackImportState.REJECTED,
                if(countsBytes || reported>=0 || totalBytes!=null) copied else null,totalBytes))
            val category=if(error is PackPolicyRejected) PackImportFailure.POLICY_REJECTED else when(stage) {
                PackImportStage.SELECTED_DOCUMENT_COPY->PackImportFailure.DOCUMENT_READ_FAILED
                PackImportStage.SNAPSHOT_COPY->PackImportFailure.SNAPSHOT_COPY_FAILED
                PackImportStage.ARCHIVE_AUDIT->PackImportFailure.ARCHIVE_REJECTED
                PackImportStage.SIGNATURE_AUTHENTICATION->PackImportFailure.SIGNATURE_OR_MANIFEST_REJECTED
                PackImportStage.MANIFEST_PROFILE_POLICY->PackImportFailure.MANIFEST_PROFILE_REJECTED
                PackImportStage.PAYLOAD_INTEGRITY->PackImportFailure.PAYLOAD_REJECTED
                PackImportStage.DATABASE_INDEX->PackImportFailure.DATABASE_INDEX_REJECTED
                PackImportStage.REGISTRY_COMMIT->PackImportFailure.REGISTRY_CHANGE_REJECTED
            }
            throw PackImportRejected(category,error)
        }
    }
}
