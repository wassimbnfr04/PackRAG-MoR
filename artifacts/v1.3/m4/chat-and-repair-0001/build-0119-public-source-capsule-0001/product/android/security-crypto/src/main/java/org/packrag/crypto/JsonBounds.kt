package org.packrag.crypto

/** Applied only after raw authentication, before recursive JCS/JSON parsers. */
object JsonBounds {
    const val MAX_DEPTH = 32
    fun check(raw: ByteArray) {
        val stack = ArrayList<Int>(); var quoted = false; var escaped = false
        for(byte in raw) {
            val value = byte.toInt() and 255
            if(quoted) {
                if(escaped) escaped = false
                else if(value == 92) escaped = true
                else if(value == 34) quoted = false
            } else when(value) {
                34 -> quoted = true
                123,91 -> { stack.add(value); require(stack.size <= MAX_DEPTH) { "Authenticated JSON exceeds nesting limit" } }
                125,93 -> require(stack.isNotEmpty() && stack.removeAt(stack.lastIndex) == if(value == 125) 123 else 91) { "Unbalanced authenticated JSON" }
            }
        }
        require(!quoted && stack.isEmpty()) { "Unterminated authenticated JSON" }
    }
}
