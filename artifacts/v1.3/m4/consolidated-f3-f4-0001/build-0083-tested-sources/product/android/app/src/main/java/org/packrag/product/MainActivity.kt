package org.packrag.product

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
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
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.Composable
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
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
            var diagnosticsEnabled by rememberSaveable { mutableStateOf(false) }
            var sourceEvidenceId by rememberSaveable { mutableStateOf<String?>(null) }
            var sourceResultId by rememberSaveable { mutableStateOf<String?>(null) }
            var managing by rememberSaveable { mutableStateOf(false) }
            var checkingAssets by rememberSaveable { mutableStateOf(false) }
            var selectedAssetSlot by rememberSaveable { mutableStateOf<String?>(null) }
            val canonical=capturedSource(state.answer,state.completedResultId,sourceEvidenceId,sourceResultId)
            LaunchedEffect(state.completedResultId) {
                if(state.completedResultId==null || state.completedResultId!=sourceResultId) {
                    sourceEvidenceId=null;sourceResultId=null
                }
            }
            BackHandler(enabled=canonical!=null || managing || checkingAssets) {
                // Consume local Back while verification runs; never cancel a pack commit.
                if(!state.busy) {
                    if(checkingAssets) checkingAssets=false
                    else if(canonical!=null) { sourceEvidenceId=null;sourceResultId=null }
                    else if(state.detailRequest!=null) model.closeDetails()
                    else managing=false
                }
            }
            val picker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri -> if (uri != null) model.importPack(uri) }
            val assetPicker=rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
                val slot=LocalAssetSlot.entries.singleOrNull{it.name==selectedAssetSlot};selectedAssetSlot=null
                if(uri!=null && slot!=null)model.importLocalAsset(slot,uri)
            }
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
                    Column(Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(24.dp)) {
                        Text("PackRAG", style = MaterialTheme.typography.headlineMedium)
                        Text("Local processing · app has no network permission",modifier = Modifier.testTag("local-processing"))
                        PackImportScreen(state.packImportEvents)
                        if(checkingAssets) {
                            Button(onClick={checkingAssets=false},enabled=!state.busy,modifier=Modifier.testTag("local-assets-back")) { Text("Back to answer") }
                            LocalAssetsScreen(state.localAssets,state.busy,model::checkLocalAssets,state.localAssetImport,state.message,
                                onImport={slot->selectedAssetSlot=slot.name;assetPicker.launch(arrayOf("*/*"))},onCancelImport=model::cancelLocalAssetImport)
                        } else if (canonical != null) {
                            Button(onClick = { sourceEvidenceId=null;sourceResultId=null },enabled=!state.busy,modifier=Modifier.testTag("source-back-answer")) { Text("Back to answer") }
                            SourceScreen(canonical)
                        } else if(managing) {
                            Button(onClick = { model.closeDetails();managing = false },enabled=!state.busy,modifier=Modifier.testTag("packs-back-answer")) { Text("Back to answer") }
                            val requested=state.detailRequest
                            if(requested!=null) {
                                Button(onClick=model::closeDetails,enabled=!state.busy,modifier=Modifier.testTag("details-back-packs")) { Text("Back to installed packs") }
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
                                InstalledPackOverview(pack,LocalDate.now().toString())
                                if(authenticatedOverview(pack)==null)Text("Requested manifest SHA256: ${pack.hash}")
                                Text("Newest previously installed: ${pack.newest}")
                                Button(onClick={model.inspectPack(pack.id,pack.version,pack.hash)},enabled=!state.busy,modifier=Modifier.testTag("details-${pack.tag}")) { Text("View verified details") }
                                PackControls(pack,model,state.busy)
                            }
                            }
                        } else {
                            Text(state.message)
                            ActivePackChips(state.installed,state.busy) { identity ->
                                sourceEvidenceId=null;sourceResultId=null;managing=true
                                model.inspectPack(identity.packId,identity.version,identity.manifestSha256)
                            }
                            val deviceDate = LocalDate.now().toString()
                            state.activeFreshness.filter { it.advisoryAt(deviceDate) }.forEach {
                                Text("Freshness advisory for ${it.identity.packId}@${it.identity.version}: update check due ${it.updateCheckAfter}, compared with device date $deviceDate. Evidence remains subject to normal validation.")
                            }
                            Button(onClick = { picker.launch(arrayOf("application/octet-stream", "application/zip")) }, enabled = !state.busy) { Text("Import signed KPack") }
                            Button(onClick = { sourceEvidenceId=null;sourceResultId=null; managing = true }, enabled = !state.busy,modifier=Modifier.testTag("manage-packs")) { Text("Manage packs") }
                            Button(onClick={checkingAssets=true},enabled=!state.busy,modifier=Modifier.testTag("local-assets-open")) { Text("Local assets") }
                            OutlinedTextField(value = question, onValueChange = { question = it }, label = { Text("Question") }, modifier = Modifier.testTag("query-question"), enabled = true)
                            OutlinedTextField(value = asOf, onValueChange = { asOf = it }, label = { Text("As-of date (YYYY-MM-DD)") }, modifier = Modifier.testTag("query-date"), singleLine = true)
                            Text("Default date comes from the device clock. Check it or enter the date you need.")
                            OutlinedTextField(value = jurisdiction, onValueChange = { jurisdiction = it }, label = { Text("Jurisdiction (empty = all)") }, modifier = Modifier.testTag("query-jurisdiction"), singleLine = true)
                            Row(Modifier.fillMaxWidth().heightIn(min=48.dp).testTag("query-current-law")
                                .toggleable(value=currentLaw,role=Role.Checkbox,onValueChange={currentLaw=it})) {
                                Checkbox(checked = currentLaw,onCheckedChange = null,modifier=Modifier.clearAndSetSemantics {})
                                Text("Current law only (exclude repealed/superseded)")
                            }
                            Row {
                                Button(onClick = { model.ask(question,asOf,jurisdiction,currentLaw) }, modifier = Modifier.testTag("query-submit"), enabled = question.isNotBlank()) { Text("Ask") }
                                if (state.busy && state.submission!=null && state.detailRequest==null) Button(onClick = model::cancel) { Text("Cancel") }
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
                                Button(onClick = { sourceEvidenceId=record.evidenceId;sourceResultId=state.completedResultId }) { Text("[${record.evidenceId}] ${record.title} · ${record.locator}") }
                            }
                            Button(onClick={diagnosticsEnabled=!diagnosticsEnabled},modifier=Modifier.testTag("diagnostics-toggle")) {
                                Text(if(diagnosticsEnabled) "Hide diagnostics" else "Show diagnostics")
                            }
                            if(diagnosticsEnabled) {
                                state.trace?.let { DiagnosticsPanel(it) } ?: Text("No completed query trace is available.",modifier=Modifier.testTag("diagnostics-unavailable"))
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
