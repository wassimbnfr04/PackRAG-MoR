package org.packrag.sources

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.Button
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.style.TextDirection
import org.packrag.model.*
import java.util.Locale

@Composable private fun Lines(values:List<DetailLine>,prefix:String="") { values.forEach { Text("$prefix${it.label}: ${it.value}") } }
@Composable private fun Canonical(text:String,language:String?,tag:String) {
    Text(text,modifier=Modifier.testTag(tag),style=TextStyle(textDirection=if(language?.substringBefore('-')?.lowercase(Locale.ROOT)=="ar") TextDirection.ContentOrRtl else TextDirection.ContentOrLtr))
}
@Composable fun SourceScreen(value:SourceRecord) {
    Text(value.title,style=MaterialTheme.typography.titleLarge)
    Text("Captured evidence provenance",modifier=Modifier.testTag("source-details"))
    Text("Publisher authentication, signed source assertions and answer grounding are separate. Output/citation-format checks do not establish semantic entailment or completeness. Declared license/reviewer fields are not independent approval.")
    Lines(sourceLines(value))
    Text(if(value.attribution?.snapshotPath!=null) "The packaged original snapshot's hash was verified at admission. This screen displays captured text, without opening a file or network link."
        else "No original snapshot was packaged. The original hash is a signed assertion; an external original document was not checked by this screen.")
    Text("Canonical text",style=MaterialTheme.typography.titleMedium)
    Canonical(value.canonicalText,value.canonicalLanguage,"source-canonical-text")
    val rendering=value.generatorRepresentation
    if(rendering!=null) {
        Text("Text used for generation",style=MaterialTheme.typography.titleMedium)
        Text("Language: ${rendering.language} · method: ${rendering.derivationMethod} · SHA-256: ${rendering.textSha256}")
        Text("Derivation source: ${unknown(rendering.derivationSource)} · reviewer assertion: ${unknown(rendering.reviewerId)} · reviewed at: ${unknown(rendering.reviewedAt)}")
        if(rendering.text==value.canonicalText) Text("Generation used the exact canonical text above.",modifier=Modifier.testTag("source-generator-text"))
        else Text(rendering.text,modifier=Modifier.testTag("source-generator-text"))
    } else Text("Generator representation: Unknown")
    Lines(conflictLines(value.conflicts))
    Text("Captured origins (${value.originRecords.size})",style=MaterialTheme.typography.titleMedium)
    value.originRecords.forEachIndexed { index,origin ->
        Text("Origin ${index+1}: ${origin.identity.packId}@${origin.identity.version} · ${origin.identity.manifestSha256}")
        Text("Source ${origin.chunk.sourceId} · chunk ${origin.chunk.id} · locator ${origin.chunk.locator} · publisher ${origin.chunk.publisher}")
        Text("Canonical SHA-256: ${origin.chunk.textSha256} · original SHA-256: ${origin.chunk.originalSha256}")
        Lines(attributionLines(origin.chunk.attribution)+validityLines(validityProvenance(origin.chunk))+metadataLines(origin.metadata)+conflictLines(origin.conflicts),"Origin ${index+1} · ")
        if(origin.chunk.canonicalText==value.canonicalText && origin.chunk.language==value.canonicalLanguage)
            Text("This origin's canonical bytes and language match the primary record above.")
        else Canonical(origin.chunk.canonicalText,origin.chunk.language,"source-origin-$index")
        origin.derived.forEach { derived ->
            Text("Available signed derivation: ${derived.language} · ${derived.derivationMethod} · ${derived.textSha256}; source ${unknown(derived.derivationSource)}; reviewer assertion ${unknown(derived.reviewerId)}; reviewed ${unknown(derived.reviewedAt)}. Availability does not mean it was selected for generation.")
        }
    }
}

@Composable fun PackDetailsScreen(value:PackDetails) {
    Text(value.name,style=MaterialTheme.typography.titleLarge)
    Text("Installed content freshly verified",modifier=Modifier.testTag("pack-details-verified"))
    Text("Viewing these details does not activate a version. Signature verification authenticates publisher content; source licenses, calibration and review metadata remain signed assertions.")
    Text("${value.identity.packId}@${value.identity.version} · ${value.identity.manifestSha256}")
    Text("Publisher: ${value.publisherName} · signing key: ${value.publisherKeyId}")
    Text("Domain: ${value.domain} · languages: ${value.languages.joinToString()} · jurisdictions: ${value.jurisdictions.joinToString().ifEmpty { "None declared" }}")
    Text("Released: ${value.releaseTimestamp} · update check due: ${value.updateCheckAfter}")
    Text("Verified sizes in bytes: transport ${value.transportBytes}; declared payload ${value.payloadBytes}; manifest ${value.manifestBytes}")
    Text("${value.sources.size} sources · ${value.chunkCount} chunks · calibration assertion: ${value.calibrationStatus}")
    Text("Signed embedding profile: ${value.embeddingProfileJson}")
    Text("Signed build assertions: ${value.buildJson}")
    Text("Signed calibration assertions: ${value.calibrationJson}")
    var page by remember(value) { mutableIntStateOf(0) }
    val pages=(value.sources.size+9)/10
    Text("Sources and declared licenses · page ${if(pages==0) 0 else page+1}/$pages")
    if(page>0) Button(onClick={page--}) { Text("Previous sources") }
    if(page+1<pages) Button(onClick={page++}) { Text("Next sources") }
    value.sources.drop(page*10).take(10).forEach { source ->
        Text("${source.sourceId} · ${source.title}",style=MaterialTheme.typography.titleMedium)
        Text("Publisher ${source.publisher} · language ${source.language} · jurisdiction ${unknown(source.jurisdiction)} · legal status ${unknown(source.legalStatus)}")
        Text("Original SHA-256: ${source.originalSha256} · source interval [${unknown(source.sourceFrom)}, ${unknown(source.sourceUntilExcl)})")
        Text("Authority assertion ${unknown(source.authorityRank)} · version ${unknown(source.documentVersion)} · issued ${unknown(source.issuedAt)}")
        Lines(attributionLines(source.attribution))
    }
}
