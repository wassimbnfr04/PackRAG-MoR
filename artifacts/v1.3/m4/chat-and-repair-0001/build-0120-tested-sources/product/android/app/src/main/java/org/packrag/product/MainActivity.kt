package org.packrag.product

import android.os.Bundle
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.ui.graphics.Color
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.window.DialogProperties
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.semantics
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
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

/** Local chat product; every answer still passes the v1.3 verified evidence pipeline. */
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
        val testLayout=isolatedUiLayout(BuildConfig.ALLOW_DEVELOPMENT_PACKS,intent.getStringExtra("packrag.debug.uiTestId"),
            intent.getFloatExtra("packrag.debug.uiTestFontScale",1f),intent.getIntExtra("packrag.debug.uiTestWidthDp",0))
        setTheme(android.R.style.Theme_DeviceDefault_NoActionBar)
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            ProductLayoutScope(testLayout) {
            val state by model.state.collectAsStateWithLifecycle()
            val turns by model.turns.collectAsStateWithLifecycle()
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
            val canonical=chatSource(turns,sourceResultId,sourceEvidenceId) ?: capturedSource(state.answer,state.completedResultId,sourceEvidenceId,sourceResultId)
            LaunchedEffect(state.completedResultId,turns.map{it.resultId}) {
                if(sourceResultId!=null && state.completedResultId!=sourceResultId && turns.none{it.resultId==sourceResultId}) {
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
            val dark=isSystemInDarkTheme()
            MaterialTheme(colorScheme=if(dark) darkColorScheme(primary=Color(0xFFE8E8E8),onPrimary=Color(0xFF151515),surface=Color(0xFF181818),background=Color(0xFF181818),surfaceContainer=Color(0xFF2B2B2B))
                else lightColorScheme(primary=Color(0xFF202020),onPrimary=Color.White,surface=Color.White,background=Color.White,surfaceContainer=Color(0xFFF1F1F1))) {
                Surface(modifier=Modifier.fillMaxSize(),color=MaterialTheme.colorScheme.background) {
                androidx.compose.foundation.layout.Box {
                Surface(modifier=(if(testLayout!=null) Modifier.widthIn(max=testLayout.maximumWidthDp.dp) else Modifier).fillMaxSize().safeDrawingPadding().imePadding().testTag("product-shell")) {
                    state.decision?.let { decision ->
                        val removal = decision.kind == "REMOVE"
                        AlertDialog(modifier=if(testLayout!=null) Modifier.widthIn(max=testLayout.maximumWidthDp.dp) else Modifier,
                            properties=DialogProperties(usePlatformDefaultWidth=testLayout==null),onDismissRequest = { if(!state.busy) model.cancelDecision() },
                            title = { Text(if(removal) "Remove installed version?" else "Older content") },
                            text = { Column(Modifier.verticalScroll(rememberScrollState())) { Text(if(removal) "Remove ${decision.id}@${decision.version}? If active, this pack will be deactivated. No other version will be activated automatically."
                                else "Activate ${decision.id}@${decision.version}? Newest previously installed: ${decision.newest}. This version is older than, or shares the version number of, the newest content previously installed. Recent changes may be missing.") } },
                            confirmButton = { TextButton(onClick = model::confirmDecision, enabled = !state.busy, modifier = Modifier.heightIn(min=48.dp).testTag("confirm-pack-change")) { Text(if(removal) "Remove version" else "Activate older content") } },
                            dismissButton = { TextButton(onClick = model::cancelDecision, enabled = !state.busy, modifier = Modifier.heightIn(min=48.dp).testTag("cancel-pack-change")) { Text("Cancel change") } })
                    }
                    if(!checkingAssets && canonical==null && !managing) {
                        ChatScreen(state,turns,question,{question=it},asOf,{asOf=it},jurisdiction,{jurisdiction=it},currentLaw,{currentLaw=it},
                            onAsk={model.ask(question,asOf,jurisdiction,currentLaw);if(model.state.value.submission!=null)question=""},onCancel=model::cancel,
                            onNewChat={model.newChat();question="";sourceEvidenceId=null;sourceResultId=null;diagnosticsEnabled=false},
                            onPacks={sourceEvidenceId=null;sourceResultId=null;managing=true},onAssets={checkingAssets=true},
                            onImport={picker.launch(arrayOf("application/octet-stream","application/zip"))},
                            onSource={id,source->sourceEvidenceId=source.evidenceId;sourceResultId=id},
                            onInspect={identity->managing=true;model.inspectPack(identity.packId,identity.version,identity.manifestSha256)},
                            diagnosticsEnabled=diagnosticsEnabled,onDiagnostics={diagnosticsEnabled=!diagnosticsEnabled},testLayout=testLayout)
                    } else Column(Modifier.testTag("product-body").fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)) {
                        Text("PackRAG", style = MaterialTheme.typography.headlineMedium,modifier=Modifier.semantics { heading() })
                        testLayout?.let { Text("ISOLATED UI TEST: ${it.maximumWidthDp}dp / ${it.fontScale}x font scale; phone settings unchanged",modifier=Modifier.testTag("ui-test-layout")) }
                        Text("Local processing · app has no network permission",modifier = Modifier.testTag("local-processing"))
                        PackImportScreen(state.packImportEvents)
                        if(checkingAssets) {
                            ProductButton(onClick={checkingAssets=false},enabled=!state.busy,modifier=Modifier.testTag("local-assets-back")) { Text("Back to answer") }
                            LocalAssetsScreen(state.localAssets,state.busy,model::checkLocalAssets,state.localAssetImport,state.message,
                                onImport={slot->selectedAssetSlot=slot.name;assetPicker.launch(arrayOf("*/*"))},onCancelImport=model::cancelLocalAssetImport)
                        } else if (canonical != null) {
                            ProductButton(onClick = { sourceEvidenceId=null;sourceResultId=null },enabled=!state.busy,modifier=Modifier.testTag("source-back-answer")) { Text("Back to answer") }
                            SourceScreen(canonical)
                        } else if(managing) {
                            ProductButton(onClick = { model.closeDetails();managing = false },enabled=!state.busy,modifier=Modifier.testTag("packs-back-answer")) { Text("Back to answer") }
                            val requested=state.detailRequest
                            if(requested!=null) {
                                ProductButton(onClick=model::closeDetails,enabled=!state.busy,modifier=Modifier.testTag("details-back-packs")) { Text("Back to installed packs") }
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
                            Text("Installed packs", style = MaterialTheme.typography.titleLarge,modifier=Modifier.semantics { heading() })
                            Text(state.message,modifier=Modifier.testTag("operation-status").semantics { liveRegion=LiveRegionMode.Polite })
                            if(state.installed.isEmpty()) Text("No installed versions.")
                            state.installed.forEach { pack ->
                                Text(pack.tag, style = MaterialTheme.typography.titleMedium)
                                InstalledPackOverview(pack,LocalDate.now().toString())
                                if(authenticatedOverview(pack)==null)Text("Requested manifest SHA256: ${pack.hash}")
                                Text("Newest previously installed: ${pack.newest}")
                                ProductButton(onClick={model.inspectPack(pack.id,pack.version,pack.hash)},enabled=!state.busy,modifier=Modifier.testTag("details-${pack.tag}").semantics { contentDescription="View verified details for ${pack.tag}" }) { Text("View verified details") }
                                PackControls(pack,model,state.busy)
                            }
                            }
                        }
                    }
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
        ProductButton(onClick={model.deactivate(pack.id)},enabled=!busy,modifier=Modifier.testTag("deactivate-${pack.tag}").semantics { contentDescription="Deactivate ${pack.tag}" }) { Text("Deactivate") }
        if(pack.previous!=null) ProductButton(onClick={model.rollback(pack.id)},enabled=!busy,modifier=Modifier.testTag("rollback-${pack.tag}").semantics { contentDescription="Rollback ${pack.tag}" }) { Text("Roll back to ${pack.previous}") }
    } else ProductButton(onClick={model.activate(pack.id,pack.version)},enabled=!busy,modifier=Modifier.testTag("activate-${pack.tag}").semantics { contentDescription="Activate ${pack.tag}" }) { Text("Activate") }
    ProductButton(onClick={model.requestRemove(pack.id,pack.version)},enabled=!busy,modifier=Modifier.testTag("remove-${pack.tag}").semantics { contentDescription="Remove ${pack.tag}" }) { Text("Remove") }
}
