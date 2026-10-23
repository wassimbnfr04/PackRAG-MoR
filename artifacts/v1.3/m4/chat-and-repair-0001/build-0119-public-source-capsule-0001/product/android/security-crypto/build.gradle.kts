plugins { id("com.android.library") }
android {
    namespace = "org.packrag.crypto"
    compileSdk = 37
    defaultConfig { minSdk = 28 }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    testOptions { unitTests.all { it.systemProperty("packrag.repo", rootProject.projectDir.resolve("../..").canonicalPath) } }
}
dependencies {
    implementation("com.google.crypto.tink:tink-android:1.23.0")
    implementation("io.github.erdtman:java-json-canonicalization:1.1")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20250517")
}
