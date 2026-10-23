plugins { id("com.android.library");id("org.jetbrains.kotlin.plugin.compose") }
android {
    namespace="org.packrag.sources"
    compileSdk=37
    defaultConfig { minSdk=28 }
    buildFeatures { compose=true }
    compileOptions { sourceCompatibility=JavaVersion.VERSION_17;targetCompatibility=JavaVersion.VERSION_17 }
}
dependencies {
    implementation(project(":core-model"))
    implementation(platform("androidx.compose:compose-bom:2026.09.00"))
    implementation("androidx.compose.material3:material3")
    // Library configurations resolve independently: share the app's frozen UI graph.
    implementation("androidx.activity:activity-compose:1.13.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.11.0")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.11.0")
    testImplementation("junit:junit:4.13.2")
}
