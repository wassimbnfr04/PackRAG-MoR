package org.packrag.product

import androidx.compose.runtime.Composable
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag

@Composable fun LocalAssetsScreen(statuses:List<LocalAssetStatus>,busy:Boolean,onCheck:()->Unit) {
    Text("Local assets",style=MaterialTheme.typography.titleLarge,modifier=Modifier.testTag("local-assets-title"))
    Text("These files stay on this device. A check verifies size and SHA256 without loading either model.")
    Text("Statuses describe the last completed check. Model loading independently verifies the pinned files again.")
    Button(onClick=onCheck,enabled=!busy,modifier=Modifier.testTag("local-assets-check")) { Text(if(busy) "Checking files…" else "Check local files") }
    statuses.forEach { status ->
        val slot=status.spec.slot
        Text(slot.label,style=MaterialTheme.typography.titleMedium)
        Text(slot.relativePath)
        Text(localAssetGuidance(status.condition),modifier=Modifier.testTag("local-asset-${slot.name}"))
        Text("Expected size: ${status.spec.bytes} bytes")
        status.observedBytes?.let { Text("Observed size: $it bytes") }
        Text("Expected SHA256: ${status.spec.sha256}")
        status.checkedAt?.let { Text("Completed check: $it") }
    }
    Text("Use the exact files listed above. Local answers require all four pinned assets.")
}
