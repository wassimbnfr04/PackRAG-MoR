package org.packrag.product

import androidx.compose.runtime.Composable
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag

@Composable fun LocalAssetsScreen(statuses:List<LocalAssetStatus>,busy:Boolean,onCheck:()->Unit,
    importing:LocalAssetImportUi?=null,message:String="",onImport:(LocalAssetSlot)->Unit={},onCancelImport:()->Unit={}) {
    Text("Local assets",style=MaterialTheme.typography.titleLarge,modifier=Modifier.testTag("local-assets-title"))
    Text("These files stay on this device. A check verifies size and SHA256 without loading either model.")
    Text("Statuses describe the last completed check. Model loading independently verifies the pinned files again.")
    if(message.isNotEmpty())Text(message,modifier=Modifier.testTag("local-assets-message"))
    importing?.let { current ->
        Text("Importing ${current.slot.label}")
        val stage=when(current.stage) {
            null->"Preparing"
            LocalAssetImportStage.COPYING->"Copying"
            LocalAssetImportStage.SYNCING->"Saving copied file"
            LocalAssetImportStage.VERIFYING->"Verifying copied file"
            LocalAssetImportStage.COMMITTING->"Installing verified file"
            LocalAssetImportStage.COMMITTED->"Installation completed"
        }
        Text("$stage · ${current.copiedBytes} / ${current.expectedBytes} bytes",modifier=Modifier.testTag("local-asset-import-progress"))
        LinearProgressIndicator(progress={current.copiedBytes.toFloat()/current.expectedBytes},modifier=Modifier.testTag("local-asset-import-indicator"))
        Button(onClick=onCancelImport,enabled=!current.cancelRequested,modifier=Modifier.testTag("local-asset-import-cancel")){Text(if(current.cancelRequested) "Waiting for cancellation…" else "Cancel import")}
    }
    Button(onClick=onCheck,enabled=!busy,modifier=Modifier.testTag("local-assets-check")) { Text(if(busy && importing==null) "Checking files…" else "Check local files") }
    statuses.forEach { status ->
        val slot=status.spec.slot
        Text(slot.label,style=MaterialTheme.typography.titleMedium)
        Text(slot.relativePath)
        Text(localAssetGuidance(status.condition),modifier=Modifier.testTag("local-asset-${slot.name}"))
        Text("Expected size: ${status.spec.bytes} bytes")
        status.observedBytes?.let { Text("Observed size: $it bytes") }
        Text("Expected SHA256: ${status.spec.sha256}")
        status.checkedAt?.let { Text("Completed check: $it") }
        Button(onClick={onImport(slot)},enabled=!busy,modifier=Modifier.testTag("local-asset-import-${slot.name}")){Text("Choose ${slot.label} file")}
    }
    Text("Use the exact files listed above. Local answers require all four pinned assets.")
    Text("A selected file is copied into this app's private storage and verified before installation. Cancelling the file picker leaves your files and completed answer unchanged.")
}
