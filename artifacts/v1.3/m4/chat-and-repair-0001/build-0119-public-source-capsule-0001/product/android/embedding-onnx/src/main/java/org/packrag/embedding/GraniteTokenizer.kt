package org.packrag.embedding

import com.google.gson.JsonParser
import com.google.gson.stream.JsonReader
import com.google.gson.stream.JsonToken
import java.io.File
import java.security.MessageDigest
import java.util.regex.Pattern

/** Implements only the hash-pinned Granite BPE contract; parity is a hard gate. */
class GraniteTokenizer(file: File, expectedSha256: String) {
    private val vocab = HashMap<String, Int>()
    private val merges = HashMap<Pair<String, String>, Int>()
    private data class Added(val content: String, val id: Int, val singleWord: Boolean)
    private val added = ArrayList<Added>()
    private lateinit var split: Pattern
    private var ignoreMerges = false
    private val byteChars = Array(256) { "" }

    init {
        require(fileSha256(file) == expectedSha256) { "Tokenizer asset hash mismatch" }
        val byteValues = ((33..126).toList() + (161..172).toList() + (174..255).toList()).toMutableList()
        val bytePoints = byteValues.toMutableList()
        var extra = 0
        for (value in 0..255) if (value !in byteValues) {
            byteValues.add(value); bytePoints.add(256 + extra++)
        }
        byteValues.indices.forEach { byteChars[byteValues[it]] = bytePoints[it].toChar().toString() }
        file.reader(Charsets.UTF_8).use { source ->
            JsonReader(source).use { reader ->
                reader.beginObject()
                while (reader.hasNext()) when (reader.nextName()) {
                    "normalizer" -> { require(reader.peek() == JsonToken.NULL); reader.nextNull() }
                    "pre_tokenizer" -> {
                        val node = JsonParser.parseReader(reader).asJsonObject
                        require(node.get("type").asString == "Sequence")
                        val pieces = node.getAsJsonArray("pretokenizers")
                        require(pieces.size() == 2)
                        val first = pieces[0].asJsonObject
                        val second = pieces[1].asJsonObject
                        require(first.get("type").asString == "Split" && first.get("behavior").asString == "Isolated")
                        require(!first.get("invert").asBoolean && second.get("type").asString == "ByteLevel")
                        require(!second.get("add_prefix_space").asBoolean && !second.get("use_regex").asBoolean)
                        // Android ICU already uses Unicode character classes and rejects
                        // this desktop-only flag. Keep the pinned regex unchanged.
                        val flags = if (System.getProperty("java.vm.name") == "Dalvik") 0 else Pattern.UNICODE_CHARACTER_CLASS
                        split = Pattern.compile(first.getAsJsonObject("pattern").get("Regex").asString, flags)
                    }
                    "added_tokens" -> {
                        reader.beginArray()
                        while (reader.hasNext()) {
                            val token = JsonParser.parseReader(reader).asJsonObject
                            require(!token.get("lstrip").asBoolean && !token.get("rstrip").asBoolean && !token.get("normalized").asBoolean)
                            added.add(Added(token.get("content").asString, token.get("id").asInt, token.get("single_word").asBoolean))
                        }
                        reader.endArray()
                    }
                    "model" -> {
                        reader.beginObject()
                        while (reader.hasNext()) when (reader.nextName()) {
                            "type" -> require(reader.nextString() == "BPE")
                            "dropout", "unk_token", "continuing_subword_prefix", "end_of_word_suffix" -> {
                                require(reader.peek() == JsonToken.NULL); reader.nextNull()
                            }
                            "fuse_unk", "byte_fallback" -> require(!reader.nextBoolean())
                            "ignore_merges" -> ignoreMerges = reader.nextBoolean()
                            "vocab" -> {
                                reader.beginObject()
                                while (reader.hasNext()) vocab[reader.nextName()] = reader.nextInt()
                                reader.endObject()
                            }
                            "merges" -> {
                                reader.beginArray()
                                var rank = 0
                                while (reader.hasNext()) {
                                    reader.beginArray()
                                    val left = reader.nextString(); val right = reader.nextString()
                                    require(!reader.hasNext()); reader.endArray()
                                    require(merges.put(left to right, rank++) == null)
                                }
                                reader.endArray()
                            }
                            else -> error("Unsupported BPE model field")
                        }
                        reader.endObject()
                    }
                    "post_processor" -> {
                        val processor = JsonParser.parseReader(reader).asJsonObject
                        require(processor.get("type").asString == "TemplateProcessing")
                        val single = processor.getAsJsonArray("single")
                        require(single.size() == 3)
                        require(single[0].asJsonObject.getAsJsonObject("SpecialToken").get("id").asString == "<|startoftext|>")
                        require(single[1].asJsonObject.getAsJsonObject("Sequence").get("id").asString == "A")
                        require(single[2].asJsonObject.getAsJsonObject("SpecialToken").get("id").asString == "<|return|>")
                    }
                    else -> reader.skipValue() // decoder/padding/truncation do not modify single untruncated encode.
                }
                reader.endObject()
            }
        }
        require(vocab.size == 179934 && merges.size == 413540 && added.size == 66 && ::split.isInitialized)
        require(added.first { it.content == "<|startoftext|>" }.id == 179934)
        require(added.first { it.content == "<|return|>" }.id == 179938)
        added.sortByDescending { it.content.length }
    }

    fun encode(text: String): IntArray {
        val output = ArrayList<Int>()
        output.add(179934)
        var plainStart = 0
        var position = 0
        while (position < text.length) {
            val token = added.firstOrNull { item -> text.startsWith(item.content, position) &&
                (!item.singleWord || ((position == 0 || !word(text.codePointBefore(position))) &&
                 (position + item.content.length == text.length || !word(text.codePointAt(position + item.content.length))))) }
            if (token != null) {
                encodeOrdinary(text.substring(plainStart, position), output)
                output.add(token.id)
                position += token.content.length
                plainStart = position
            } else position += Character.charCount(text.codePointAt(position))
        }
        encodeOrdinary(text.substring(plainStart), output)
        output.add(179938)
        return output.toIntArray()
    }

    private fun word(point: Int) = Character.isLetterOrDigit(point) || point == '_'.code ||
        Character.getType(point) in setOf(Character.NON_SPACING_MARK.toInt(), Character.COMBINING_SPACING_MARK.toInt())

    private fun encodeOrdinary(text: String, output: MutableList<Int>) {
        val matcher = split.matcher(text)
        var position = 0
        while (matcher.find()) {
            if (matcher.start() > position) encodePiece(text.substring(position, matcher.start()), output)
            encodePiece(matcher.group(), output)
            position = matcher.end()
        }
        if (position < text.length) encodePiece(text.substring(position), output)
    }

    private fun encodePiece(text: String, output: MutableList<Int>) {
        if (text.isEmpty()) return
        val parts = text.toByteArray(Charsets.UTF_8).map { byteChars[it.toInt() and 255] }.toMutableList()
        val entire = parts.joinToString("")
        if (ignoreMerges && vocab.containsKey(entire)) { output.add(vocab.getValue(entire)); return }
        while (parts.size > 1) {
            val ranks = (0 until parts.lastIndex).map { merges[parts[it] to parts[it + 1]] ?: Int.MAX_VALUE }
            val minimum = ranks.minOrNull() ?: break
            if (minimum == Int.MAX_VALUE) break
            val index = ranks.indexOf(minimum)
            parts[index] = parts[index] + parts[index + 1]
            parts.removeAt(index + 1)
        }
        parts.forEach { output.add(vocab.getValue(it)) }
    }
}

fun fileSha256(file: File): String {
    val digest = MessageDigest.getInstance("SHA-256")
    file.inputStream().use { stream ->
        val buffer = ByteArray(65536)
        while (true) { val count = stream.read(buffer); if (count < 0) break; digest.update(buffer, 0, count) }
    }
    return digest.digest().joinToString("") { "%02x".format(it.toInt() and 255) }
}
