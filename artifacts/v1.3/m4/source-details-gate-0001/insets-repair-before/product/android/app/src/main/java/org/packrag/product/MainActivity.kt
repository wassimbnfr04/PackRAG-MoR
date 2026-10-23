package org.packrag.product

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.TextButton
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.Composable
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.packrag.model.SourceRecord
import org.packrag.sources.SourceScreen
import org.packrag.sources.PackDetailsScreen
import java.time.LocalDate

/** Buffered Android walking slice. Full screens/lifecycle hardening are M3/M4. */
class MainActivity : ComponentActivity() {
    private val model by viewModels<PackRagViewModel> { object : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            require(modelClass == PackRagViewModel::class.java)
            val root = ProductConfiguration.launchRoot(application,intent)
            return PackRagViewModel(application,root) as T
        }
    } }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            val state by model.state.collectAsStateWithLifecycle()
            var question by rememberSaveable { mutableStateOf("") }
            var asOf by rememberSaveable { mutableStateOf(LocalDate.now().toString()) }
            var jurisdiction by rememberSaveable { mutableStateOf("") }
            var currentLaw by rememberSaveable { mutableStateOf(false) }
            var source by remember { mutableStateOf<SourceRecord?>(null) }
            var managing by remember { mutableStateOf(false) }
            LaunchedEffect(state.answer,state.trace) { source = null }
            val picker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri -> if (uri != null) model.importPack(uri) }
            MaterialTheme {
                Surface {
                    state.decision?.let { decision ->
                        val removal = decision.kind == "REMOVE"
                        AlertDialog(onDismissRequest = { if(!state.busy) model.cancelDecision() },
                            title = { Text(if(removal) "Remove installed version?" else "Older content") },
                            text = { Text(if(removal) "Remove ${decision.id}@${decision.version}? If active, this pack will be deactivated. No other version will be activated automatically."
                                else "Activate ${decision.id}@${decision.version}? Newest previously installed: ${decision.newest}. This version is older than, or shares the version number of, the newest content previously installed. Recent changes may be missing.") },
                            confirmButton = { TextButton(onClick = model::confirmDecision, enabled = !state.busy, modifier = Modifier.testTag("confirm-pack-change")) { Text(if(removal) "Remove version" else "Activate older content") } },
                            dismissButton = { TextButton(onClick = model::cancelDecision, enabled = !state.busy, modifier = Modifier.testTag("cancel-pack-change")) { Text("Cancel change") } })
                    }
                    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp)) {
                        Text("PackRAG", style = MaterialTheme.typography.headlineMedium)
                        Text("Local processing · app has no network permission",modifier = Modifier.testTag("local-processing"))
                        val canonical = source
                        if (canonical != null) {
                            Button(onClick = { source = null }) { Text("Back to answer") }
                            SourceScreen(canonical)
                        } else if(managing) {
                            Button(onClick = { managing = false }) { Text("Back to answer") }
                            val requested=state.detailRequest
                            if(requested!=null) {
                                Button(onClick=model::closeDetails,enabled=!state.busy) { Text("Back to installed packs") }
                                Text("Requested: ${requested.packId}@${requested.version} · ${requested.manifestSha256}")
                                if(state.busy) Text("Reverifying installed pack details…")
                                state.detailsError?.let { Text("Pack details verification failed: $it",modifier=Modifier.testTag("pack-details-error")) }
                                state.details?.let { details ->
                                    PackDetailsScreen(details)
                                    state.installed.singleOrNull { it.id==requested.packId && it.version==requested.version && it.hash==requested.manifestSha256 }?.let {
                                        Text(if(it.active) "Currently active" else "Currently inactive")
                                        PackControls(it,model,state.busy)
                                    }
                                }
                            } else {
                            Text("Installed packs", style = MaterialTheme.typography.titleLarge)
                            Text(state.message)
                            if(state.installed.isEmpty()) Text("No installed versions.")
                            state.installed.forEach { pack ->
                                Text(pack.tag, style = MaterialTheme.typography.titleMedium)
                                Text(if(pack.active) "Active · verified" else if(pack.trust == "VERIFIED") "Inactive · verified at install; rechecked before activation" else "Inactive · verification failed")
                                Text("Manifest SHA256: ${pack.hash}")
                                Text("Newest previously installed: ${pack.newest}")
                                Button(onClick={model.inspectPack(pack.id,pack.version,pack.hash)},enabled=!state.busy,modifier=Modifier.testTag("details-${pack.tag}")) { Text("View verified details") }
                                PackControls(pack,model,state.busy)
                            }
                            }
                        } else {
                            Text(state.message)
                            state.packs.forEach { Text(it) }
                            val deviceDate = LocalDate.now().toString()
                            state.activeFreshness.filter { it.advisoryAt(deviceDate) }.forEach {
                                Text("Freshness advisory for ${it.identity.packId}@${it.identity.version}: update check due ${it.updateCheckAfter}, compared with device date $deviceDate. Evidence remains subject to normal validation.")
                            }
                            Button(onClick = { picker.launch(arrayOf("application/octet-stream", "application/zip")) }, enabled = !state.busy) { Text("Import signed KPack") }
                            Button(onClick = { source = null; managing = true }, enabled = !state.busy) { Text("Manage packs") }
                            OutlinedTextField(value = question, onValueChange = { question = it }, label = { Text("Question") }, modifier = Modifier.testTag("query-question"), enabled = true)
                            OutlinedTextField(value = asOf, onValueChange = { asOf = it }, label = { Text("As-of date (YYYY-MM-DD)") }, modifier = Modifier.testTag("query-date"), singleLine = true)
                            Text("Default date comes from the device clock. Check it or enter the date you need.")
                            OutlinedTextField(value = jurisdiction, onValueChange = { jurisdiction = it }, label = { Text("Jurisdiction (empty = all)") }, modifier = Modifier.testTag("query-jurisdiction"), singleLine = true)
                            Row {
                                Checkbox(checked = currentLaw,onCheckedChange = { currentLaw = it },modifier = Modifier.testTag("query-current-law"))
                                Text("Current law only (exclude repealed/superseded)")
                            }
                            Row {
                                Button(onClick = { model.ask(question,asOf,jurisdiction,currentLaw) }, modifier = Modifier.testTag("query-submit"), enabled = question.isNotBlank()) { Text("Ask") }
                                if (state.busy) Button(onClick = model::cancel) { Text("Cancel") }
                            }
                            state.inputError?.let { Text("${queryInputGuidance(it)} ($it)",modifier = Modifier.testTag("query-input-error")) }
                            state.submission?.let { captured ->
                                Text("Submitted context",style = MaterialTheme.typography.titleMedium)
                                Text("Question: ${captured.query.raw}")
                                Text("As-of: ${captured.query.asOf} · Jurisdiction: ${captured.query.jurisdiction ?: "all"} · Current law only: ${captured.query.currentLaw}",modifier = Modifier.testTag("submitted-query-context"))
                                captured.packs.forEach {
                                    Text("Submitted pack: ${it.identity.packId}@${it.identity.version} · ${it.identity.manifestSha256}")
                                    if(it.advisoryAt(captured.query.asOf)) Text("Freshness advisory: update check due ${it.updateCheckAfter}, compared with submitted date ${captured.query.asOf}. This is advisory; it does not reject otherwise valid evidence.",modifier = Modifier.testTag("submitted-freshness"))
                                }
                            }
                            state.answer?.let { Text(answerGuidance(it.state),modifier = Modifier.testTag("answer-guidance")) }
                            state.answer?.text?.let { Text(it) }
                            state.answer?.sources?.forEach { record ->
                                Button(onClick = { source = record }) { Text("[${record.evidenceId}] ${record.title} · ${record.locator}") }
                            }
                        }
                    }
                }
            }
        }
    }
}

/** Both list/details use the same already-tested ViewModel consent/mutation path. */
@Composable private fun PackControls(pack:PackRow,model:PackRagViewModel,busy:Boolean) {
    if(pack.active) {
        Button(onClick={model.deactivate(pack.id)},enabled=!busy,modifier=Modifier.testTag("deactivate-${pack.tag}")) { Text("Deactivate") }
        if(pack.previous!=null) Button(onClick={model.rollback(pack.id)},enabled=!busy,modifier=Modifier.testTag("rollback-${pack.tag}")) { Text("Roll back to ${pack.previous}") }
    } else Button(onClick={model.activate(pack.id,pack.version)},enabled=!busy,modifier=Modifier.testTag("activate-${pack.tag}")) { Text("Activate") }
    Button(onClick={model.requestRemove(pack.id,pack.version)},enabled=!busy,modifier=Modifier.testTag("remove-${pack.tag}")) { Text("Remove") }
}
