package org.packrag.product

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import org.packrag.packs.PackImportEvent
import org.packrag.packs.PackImportStage
import org.packrag.packs.PackImportState

fun packImportStageLabel(stage:PackImportStage):String = when(stage) {
    PackImportStage.SELECTED_DOCUMENT_COPY->"Selected document copy (transport bytes)"
    PackImportStage.SNAPSHOT_COPY->"Private verification copy (transport bytes)"
    PackImportStage.ARCHIVE_AUDIT->"Archive safety audit"
    PackImportStage.SIGNATURE_AUTHENTICATION->"Signature and signed-manifest authentication"
    PackImportStage.MANIFEST_PROFILE_POLICY->"Manifest, profile and policy validation"
    PackImportStage.PAYLOAD_INTEGRITY->"Payload verification (uncompressed bytes)"
    PackImportStage.DATABASE_INDEX->"Knowledge database and dense index validation"
    PackImportStage.REGISTRY_COMMIT->"Registry activation"
}
fun packImportEventLabel(event:PackImportEvent):String {
    val state=when(event.state) {
        PackImportState.STARTED->"Started"
        PackImportState.PROGRESS->"In progress"
        PackImportState.PASSED->"Completed"
        PackImportState.REJECTED->"Failed"
        PackImportState.AWAITING_CONSENT->"Waiting for older-content confirmation"
        PackImportState.COMMITTED->"Database committed; finishing activation"
        PackImportState.RECOVERY_REQUIRED->"Completion uncertain; rechecking stored state"
    }
    val bytes=event.bytes?.let { " · $it"+(event.totalBytes?.let { total->" / $total" } ?: " (total unknown)")+" bytes" } ?: ""
    return packImportStageLabel(event.stage)+": "+state+bytes
}

@Composable fun PackImportScreen(events:List<PackImportEvent>) {
    if(events.isEmpty()) return
    Text("Observed pack import",style=MaterialTheme.typography.titleMedium,modifier=Modifier.testTag("pack-import-title"))
    Text("Each completed stage records its own successful checks. Transport copies and uncompressed payload bytes are separate; no overall percentage is estimated.")
    events.forEach { event -> Text(packImportEventLabel(event),modifier=Modifier
        .testTag("pack-import-${event.stage.name}").semantics { liveRegion=LiveRegionMode.Polite }) }
}
