plugins { id("com.android.library") }
android {
    namespace = "org.packrag.embedding"
    compileSdk = 37
    defaultConfig { minSdk = 28; ndk { abiFilters += "arm64-v8a" } }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    testOptions {
        unitTests.all {
            it.systemProperty("packrag.repo", rootProject.projectDir.resolve("../..").canonicalPath)
            it.maxHeapSize = "768m"
        }
    }
}
dependencies {
    implementation(project(":core-model"))
    implementation("com.microsoft.onnxruntime:onnxruntime-android:1.30.0")
    implementation("com.google.code.gson:gson:2.14.0")
    testImplementation("junit:junit:4.13.2")
}
