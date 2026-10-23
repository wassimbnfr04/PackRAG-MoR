package org.packrag.model

/** Presence only; preserve source bytes and avoid JVM/Android whitespace drift. */
object SourceText {
    fun nonBlank(value:String?):Boolean = value!=null && value.codePoints().anyMatch { !QueryUnicode.isWhitespace(it) }
}
