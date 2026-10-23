package org.packrag.embedding

import com.google.gson.JsonParser
import java.io.File
import org.junit.Assert.assertArrayEquals
import org.junit.Test

class TokenizerParityTest {
    @Test fun exactOfficialTokenizerParity() {
        val root = File(requireNotNull(System.getProperty("packrag.repo")))
        val reference = File(root, "artifacts/v1.3/m2/parity-reference-0002/parity-reference.json")
            .reader(Charsets.UTF_8).use { JsonParser.parseReader(it).asJsonObject }
        val tokenizer = GraniteTokenizer(File(root, "models/v1.3/granite/tokenizer.json"),
            reference.getAsJsonObject("lock").getAsJsonObject("embedder").getAsJsonObject("asset_sha256").get("tokenizer.json").asString)
        for (element in reference.getAsJsonArray("tokenizer_cases")) {
            val case = element.asJsonObject
            assertArrayEquals(case.get("id").asString, case.getAsJsonArray("ids").map { it.asInt }.toIntArray(),
                              tokenizer.encode(case.get("text").asString))
        }
    }
}
