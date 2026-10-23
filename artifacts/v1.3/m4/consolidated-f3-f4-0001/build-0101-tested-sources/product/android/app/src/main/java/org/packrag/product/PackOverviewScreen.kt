package org.packrag.product

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import org.packrag.model.PackIdentity

@Composable fun ActivePackChips(rows:List<PackRow>,busy:Boolean,onInspect:(PackIdentity)->Unit) {
    val active=activePackIdentities(rows)
    Column(Modifier.fillMaxWidth().testTag("active-packs")) {
        if(active.isEmpty())Text("No active knowledge packs.",modifier=Modifier.testTag("active-packs-empty"))
        active.forEach { identity ->
            val row=rows.single { it.identity==identity }
            AssistChip(onClick={onInspect(identity)},enabled=!busy,
                modifier=Modifier.fillMaxWidth().heightIn(min=48.dp).testTag("active-pack-${row.tag}-${row.hash}"),
                label={Text(row.tag+"\n"+(authenticatedOverview(row)?.name ?: "Recheck installed details"))})
        }
    }
}

@Composable fun InstalledPackOverview(row:PackRow,deviceDate:String) {
    Column(Modifier.fillMaxWidth().testTag("pack-overview-${row.tag}")) {
        Text(packVerificationLabel(row))
        Text(storedPackTrustLabel(row.trust))
        packOverviewLines(row,deviceDate).forEach { Text(it) }
    }
}
