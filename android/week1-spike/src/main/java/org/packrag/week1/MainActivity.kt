package org.packrag.week1

import android.app.Activity
import android.os.Bundle
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        setContentView(TextView(this).apply {
            text = "PackRAG-MoR v1.2 — Week 1 spike\n\nOffline signature and database tests run through instrumentation.\nTEST KEY ONLY — NEVER USE FOR RELEASE"
            setPadding(32, 48, 32, 32)
        })
    }
}
