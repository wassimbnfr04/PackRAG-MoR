package org.packrag.packs

import org.junit.Assert.assertThrows
import org.junit.Test

class ArchivePolicyTest {
    @Test fun dataOnlyPortablePaths() {
        listOf("manifest.json", "manifest.sig", "knowledge.sqlite", "dense.kdx", "sources/manual.txt").forEach(ArchivePolicy::safePath)
        for (path in listOf("../dense.kdx", "/sources/a.txt", "C:/a.txt", "sources\\a.txt", "sources//a.txt",
            "sources/CON.txt", "sources/e\u0301.txt", "sources/file. ", "sources/a.py", "sources/a.gguf", "prompts/a.txt", "sources/a\u0000.txt"))
            assertThrows(path, IllegalArgumentException::class.java) { ArchivePolicy.safePath(path) }
    }
}
