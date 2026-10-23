plugins { id("com.android.application") }
android {
    namespace = "org.packrag.week1"
    compileSdk = 37
    buildToolsVersion = "37.0.0"
    ndkVersion = "30.0.16248370"
    defaultConfig {
        applicationId = "org.packrag.week1"
        minSdk = 28
        targetSdk = 37
        versionCode = 1
        versionName = "1.2.0-week1"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        ndk { abiFilters += "arm64-v8a" }
    }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    testOptions { unitTests.isReturnDefaultValues = true }
}
dependencies {
    implementation("com.google.crypto.tink:tink-android:1.23.0")
    implementation("androidx.sqlite:sqlite-bundled:2.7.1")
    implementation("io.github.erdtman:java-json-canonicalization:1.1")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20250517")
    androidTestImplementation("androidx.test.ext:junit:1.3.0")
    androidTestImplementation("androidx.test:runner:1.7.0")
}
