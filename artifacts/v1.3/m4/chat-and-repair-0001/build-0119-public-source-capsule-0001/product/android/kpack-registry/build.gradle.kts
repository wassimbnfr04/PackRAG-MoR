plugins { id("com.android.library") }
android {
    namespace = "org.packrag.packs"
    compileSdk = 37
    defaultConfig { minSdk = 28; ndk { abiFilters += "arm64-v8a" } }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    testOptions { unitTests.all { it.systemProperty("packrag.repo", rootProject.projectDir.resolve("../..").canonicalPath) } }
}
dependencies {
    implementation(project(":core-model"))
    implementation(project(":security-crypto"))
    implementation("androidx.sqlite:sqlite-bundled:2.7.1")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20250517")
}
