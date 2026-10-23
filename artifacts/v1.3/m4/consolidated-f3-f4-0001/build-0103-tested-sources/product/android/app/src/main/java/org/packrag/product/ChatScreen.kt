package org.packrag.product

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.packrag.model.SourceRecord

@Composable fun ChatIcon(kind:String,modifier:Modifier=Modifier) {
    val color=MaterialTheme.colorScheme.onSurface
    Canvas(modifier.size(22.dp)) {
        val w=size.width;val h=size.height;val stroke=2.dp.toPx()
        when(kind) {
            "menu" -> for(y in listOf(.25f,.5f,.75f))drawLine(color,Offset(w*.15f,h*y),Offset(w*.85f,h*y),stroke)
            "plus" -> {drawLine(color,Offset(w*.5f,h*.15f),Offset(w*.5f,h*.85f),stroke);drawLine(color,Offset(w*.15f,h*.5f),Offset(w*.85f,h*.5f),stroke)}
            "send" -> {drawLine(color,Offset(w*.5f,h*.85f),Offset(w*.5f,h*.15f),stroke);drawLine(color,Offset(w*.15f,h*.5f),Offset(w*.5f,h*.15f),stroke);drawLine(color,Offset(w*.85f,h*.5f),Offset(w*.5f,h*.15f),stroke)}
            "stop" -> drawRect(color,topLeft=Offset(w*.2f,h*.2f),size=androidx.compose.ui.geometry.Size(w*.6f,h*.6f))
            else -> {drawCircle(color,radius=w*.34f,style=Stroke(stroke));drawCircle(color,radius=w*.10f)}
        }
    }
}

@Composable fun ChatScreen(state:UiState,turns:List<ChatTurn>,question:String,onQuestion:(String)->Unit,
    asOf:String,onDate:(String)->Unit,jurisdiction:String,onJurisdiction:(String)->Unit,currentLaw:Boolean,onCurrentLaw:(Boolean)->Unit,
    onAsk:()->Unit,onCancel:()->Unit,onNewChat:()->Unit,onPacks:()->Unit,onAssets:()->Unit,onImport:()->Unit,
    onSource:(String,SourceRecord)->Unit,onInspect:(org.packrag.model.PackIdentity)->Unit,
    diagnosticsEnabled:Boolean,onDiagnostics:()->Unit,testLayout:ProductUiLayout?) {
    var menu by rememberSaveable { mutableStateOf(false) }
    var controls by rememberSaveable { mutableStateOf(false) }
    var context by rememberSaveable { mutableStateOf(false) }
    var importDetails by rememberSaveable { mutableStateOf(false) }
    val scroll=rememberScrollState()
    val shown=if(turns.isEmpty() && state.completedResultId!=null && state.submission!=null && state.answer!=null)
        listOf(ChatTurn(state.completedResultId,state.submission,state.answer)) else turns
    LaunchedEffect(shown.lastOrNull()?.resultId,state.busy) { scroll.animateScrollTo(scroll.maxValue) }
    BoxWithConstraints(Modifier.fillMaxSize()) {
        val composerHeight=minOf(360.dp,maxOf(100.dp,maxHeight-100.dp))
        Column(Modifier.fillMaxSize()) {
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal=10.dp,vertical=4.dp),verticalAlignment=Alignment.CenterVertically) {
                IconButton(onClick={menu=!menu},modifier=Modifier.sizeIn(minWidth=48.dp,minHeight=48.dp).testTag("app-menu").semantics{contentDescription="Open app menu"}) { ChatIcon("menu") }
                TextButton(onClick=onPacks,enabled=!state.busy,modifier=Modifier.weight(1f).heightIn(min=48.dp).testTag("manage-packs")) {
                    Column(horizontalAlignment=Alignment.CenterHorizontally) {
                        Text("PackRAG",fontWeight=FontWeight.SemiBold,fontSize=20.sp,modifier=Modifier.semantics{heading()})
                        Text(if(state.packs.isEmpty()) "On device · no active pack" else "On device · ${state.packs.size} active pack${if(state.packs.size==1) "" else "s"}",fontSize=11.sp,maxLines=1)
                    }
                }
                IconButton(onClick=onNewChat,enabled=!state.busy,modifier=Modifier.sizeIn(minWidth=48.dp,minHeight=48.dp).testTag("new-chat").semantics{contentDescription="New chat"}) { ChatIcon("plus") }
            }
            if(menu) Surface(color=MaterialTheme.colorScheme.surfaceContainer,shape=RoundedCornerShape(20.dp),modifier=Modifier.padding(horizontal=12.dp).fillMaxWidth()) {
                Column(Modifier.heightIn(max=240.dp).verticalScroll(rememberScrollState()).padding(12.dp)) {
                    Text("Your local assistant",style=MaterialTheme.typography.titleMedium)
                    ProductButton(onClick={menu=false;onAssets()},enabled=!state.busy,modifier=Modifier.testTag("local-assets-open")){Text("Local model & files")}
                    ProductButton(onClick={menu=false;onImport()},enabled=!state.busy,modifier=Modifier.testTag("menu-import-kpack")){Text("Import signed knowledge pack")}
                    ProductButton(onClick=onDiagnostics,modifier=Modifier.testTag("diagnostics-toggle")){Text(if(diagnosticsEnabled) "Hide diagnostics" else "Show diagnostics")}
                    ActivePackChips(state.installed,state.busy){menu=false;onInspect(it)}
                    Text("This app processes your question locally.",fontSize=12.sp,modifier=Modifier.testTag("local-processing"))
                }
            }
            Column(Modifier.weight(1f).fillMaxWidth().testTag("product-body").verticalScroll(scroll).padding(horizontal=20.dp,vertical=12.dp),verticalArrangement=Arrangement.spacedBy(16.dp)) {
                testLayout?.let { Text("ISOLATED UI TEST: ${it.maximumWidthDp}dp / ${it.fontScale}x; phone settings unchanged",fontSize=10.sp,modifier=Modifier.testTag("ui-test-layout")) }
                if(shown.isEmpty() && !state.busy) {
                    Spacer(Modifier.height(44.dp))
                    Text("How can I help?",style=MaterialTheme.typography.headlineMedium,fontWeight=FontWeight.SemiBold)
                    Text("Choose a verified pack, then describe the device and the problem.",color=MaterialTheme.colorScheme.onSurfaceVariant)
                    if(state.packs.isEmpty()) Text("No active knowledge pack.",modifier=Modifier.testTag("active-packs-empty"))
                }
                if(state.packImportEvents.isNotEmpty()) {
                    TextButton(onClick={importDetails=!importDetails},modifier=Modifier.testTag("pack-import-details")){Text(if(importDetails) "Hide import details" else "View pack import checks")}
                    if(importDetails || state.busy) PackImportScreen(state.packImportEvents)
                }
                shown.forEach { turn ->
                    Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.End) {
                        Surface(color=MaterialTheme.colorScheme.surfaceContainer,shape=RoundedCornerShape(22.dp),modifier=Modifier.widthIn(max=320.dp).testTag("user-${turn.resultId}")) {
                            Text(turn.submission.query.raw,modifier=Modifier.padding(16.dp),fontSize=17.sp,lineHeight=25.sp)
                        }
                    }
                    Column(Modifier.fillMaxWidth().testTag("assistant-${turn.resultId}"),verticalArrangement=Arrangement.spacedBy(10.dp)) {
                        val latest=turn.resultId==state.completedResultId
                        turn.answer.text?.let{Text(it,fontSize=17.sp,lineHeight=26.sp)}
                        Text(answerGuidance(turn.answer.state),fontSize=12.sp,color=MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier=Modifier.testTag(if(latest) "answer-guidance" else "answer-guidance-${turn.resultId}").semantics{liveRegion=LiveRegionMode.Polite})
                        turn.answer.sources.forEach { source ->
                            OutlinedButton(onClick={onSource(turn.resultId,source)},enabled=!state.busy,
                                modifier=Modifier.heightIn(min=48.dp).testTag("source-${turn.resultId}-${source.evidenceId}")) {
                                Text("[${source.evidenceId}] ${source.title} · ${source.locator}")
                            }
                        }
                        TextButton(onClick={context=!context},modifier=Modifier.testTag("query-context-${turn.resultId}")){Text(if(context) "Hide answer context" else "Answer context")}
                        if(context) {
                            Text("Submitted context",fontWeight=FontWeight.Medium)
                            Text("Question: ${turn.submission.query.raw}",fontSize=12.sp)
                            Text("As-of: ${turn.submission.query.asOf} · Jurisdiction: ${turn.submission.query.jurisdiction ?: "all"} · Current law only: ${turn.submission.query.currentLaw}",fontSize=12.sp,
                                modifier=Modifier.testTag(if(latest) "submitted-query-context" else "submitted-query-context-${turn.resultId}"))
                            turn.submission.packs.forEach { pack ->
                                Text("Submitted pack: ${pack.identity.packId}@${pack.identity.version} · ${pack.identity.manifestSha256}",fontSize=12.sp)
                                if(pack.advisoryAt(turn.submission.query.asOf))Text("Freshness advisory: update check due ${pack.updateCheckAfter}, compared with submitted date ${turn.submission.query.asOf}. This is advisory; it does not reject otherwise valid evidence.",fontSize=12.sp,modifier=Modifier.testTag("submitted-freshness"))
                            }
                        }
                    }
                }
                if(state.busy && state.submission!=null) {
                    Surface(color=MaterialTheme.colorScheme.surfaceContainer,shape=RoundedCornerShape(22.dp)){Text(state.submission.query.raw,modifier=Modifier.padding(16.dp))}
                    Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(10.dp)) {
                        CircularProgressIndicator(Modifier.size(18.dp),strokeWidth=2.dp);Text("Working locally…",fontSize=14.sp)
                    }
                }
                Text(state.message,fontSize=12.sp,color=MaterialTheme.colorScheme.onSurfaceVariant,modifier=Modifier.testTag("operation-status").semantics{liveRegion=LiveRegionMode.Polite})
                state.inputError?.let { Text("${queryInputGuidance(it)} ($it)",color=MaterialTheme.colorScheme.error,modifier=Modifier.testTag("query-input-error")) }
                if(state.answer!=null && state.completedResultId==null && !state.busy)Text(answerGuidance(state.answer.state),modifier=Modifier.testTag("answer-guidance"))
                if(diagnosticsEnabled)state.trace?.let{DiagnosticsPanel(it)} ?: Text("No completed query trace is available.",modifier=Modifier.testTag("diagnostics-unavailable"))
            }
            Surface(color=MaterialTheme.colorScheme.surfaceContainer,shape=RoundedCornerShape(28.dp),modifier=Modifier.padding(horizontal=12.dp,vertical=6.dp).fillMaxWidth().heightIn(max=composerHeight).testTag("chat-composer")) {
                Column(Modifier.verticalScroll(rememberScrollState()).padding(10.dp)) {
                    OutlinedTextField(value=question,onValueChange=onQuestion,placeholder={Text("Message PackRAG")},maxLines=5,modifier=Modifier.fillMaxWidth().testTag("query-question"),
                        colors=OutlinedTextFieldDefaults.colors(focusedBorderColor=Color.Transparent,unfocusedBorderColor=Color.Transparent))
                    if(controls) {
                        OutlinedTextField(asOf,onDate,label={Text("As-of date",maxLines=1)},singleLine=true,modifier=Modifier.fillMaxWidth().testTag("query-date"))
                        Text("Date format: YYYY-MM-DD. Check the device clock.",fontSize=12.sp)
                        OutlinedTextField(jurisdiction,onJurisdiction,label={Text("Jurisdiction",maxLines=1)},singleLine=true,modifier=Modifier.fillMaxWidth().testTag("query-jurisdiction"))
                        Text("Leave jurisdiction empty to query all jurisdictions.",fontSize=12.sp)
                        Row(Modifier.fillMaxWidth().heightIn(min=48.dp).testTag("query-current-law").toggleable(currentLaw,role=Role.Checkbox,onValueChange=onCurrentLaw),verticalAlignment=Alignment.CenterVertically) {
                            Checkbox(currentLaw,null,modifier=Modifier.clearAndSetSemantics{});Text("Current law only (exclude repealed/superseded)",fontSize=14.sp)
                        }
                    }
                    Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically) {
                        IconButton(onClick=onImport,enabled=!state.busy,modifier=Modifier.sizeIn(minWidth=48.dp,minHeight=48.dp).testTag("import-kpack").semantics{contentDescription="Import signed knowledge pack"}){ChatIcon("plus")}
                        TextButton(onClick={controls=!controls},modifier=Modifier.heightIn(min=48.dp).testTag("query-controls-toggle")){Text(if(controls) "Close filters" else "Filters")}
                        Spacer(Modifier.weight(1f))
                        if(state.busy && state.submission!=null) IconButton(onClick=onCancel,modifier=Modifier.sizeIn(minWidth=48.dp,minHeight=48.dp).testTag("query-cancel").semantics{contentDescription="Cancel"}){ChatIcon("stop")}
                        else IconButton(onClick=onAsk,enabled=question.isNotBlank() && !state.busy,modifier=Modifier.sizeIn(minWidth=48.dp,minHeight=48.dp).testTag("query-submit").semantics{contentDescription="Ask"}){ChatIcon("send")}
                    }
                }
            }
        }
    }
}
