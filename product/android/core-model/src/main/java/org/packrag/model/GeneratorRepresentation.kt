package org.packrag.model

import java.security.MessageDigest
import java.util.Locale

/** Signed publisher metadata is distinct from real review/official-source verification. */
data class DerivedText(val chunkId:String,val purpose:String,val language:String,val text:String,val textSha256:String,
    val derivationMethod:String,val derivationSource:String?,val reviewerId:String?,val reviewedAt:String?)

data class GeneratorRepresentation(val text:String,val language:String,val textSha256:String,val derivationMethod:String,
    val derivationSource:String?,val reviewerId:String?,val reviewedAt:String?,val canonicalLanguage:String,val canonicalTextSha256:String)

class RepresentationFailure(val state:String):IllegalArgumentException(state)

object GeneratorRepresentations {
    private fun english(language:String)=LanguageTags.valid(language) && language.lowercase(Locale.ROOT).substringBefore('-')=="en"
    private fun hash(text:String)=MessageDigest.getInstance("SHA-256").digest(text.toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it) }
    fun select(canonical:String,canonicalHash:String,language:String,derived:List<DerivedText>):GeneratorRepresentation {
        if(!LanguageTags.valid(language)) throw RepresentationFailure("INVALID_GENERATOR_PROVENANCE")
        if(hash(canonical)!=canonicalHash) throw RepresentationFailure("GENERATOR_REPRESENTATION_HASH_MISMATCH")
        if(!SourceText.nonBlank(canonical)) throw RepresentationFailure("INVALID_GENERATOR_PROVENANCE")
        if(english(language)) return GeneratorRepresentation(canonical,language,canonicalHash,"canonical",null,null,null,language,canonicalHash)
        val eligible=derived.filter { it.purpose=="generator" && english(it.language) && it.derivationMethod in setOf("official_translation","human_reviewed_translation") }
        val preferred=eligible.filter { it.language.lowercase(Locale.ROOT)=="en" }
        val choices=preferred.ifEmpty { eligible }
        if(choices.isEmpty()) throw RepresentationFailure("NO_ELIGIBLE_GENERATOR_REPRESENTATION")
        if(choices.size!=1) throw RepresentationFailure("AMBIGUOUS_GENERATOR_REPRESENTATION")
        val row=choices.single()
        if(!SourceText.nonBlank(row.text) || !SourceText.nonBlank(row.derivationSource)) throw RepresentationFailure("INVALID_GENERATOR_PROVENANCE")
        if(row.derivationMethod=="human_reviewed_translation") {
            if(!SourceText.nonBlank(row.reviewerId) || !SourceText.nonBlank(row.reviewedAt)) throw RepresentationFailure("INVALID_GENERATOR_PROVENANCE")
            if(runCatching { TemporalDates.dateOrTimestamp(row.reviewedAt!!) }.isFailure) throw RepresentationFailure("INVALID_GENERATOR_PROVENANCE")
        }
        if(hash(row.text)!=row.textSha256) throw RepresentationFailure("GENERATOR_REPRESENTATION_HASH_MISMATCH")
        return GeneratorRepresentation(row.text,row.language,row.textSha256,row.derivationMethod,row.derivationSource,row.reviewerId,row.reviewedAt,language,canonicalHash)
    }
}
