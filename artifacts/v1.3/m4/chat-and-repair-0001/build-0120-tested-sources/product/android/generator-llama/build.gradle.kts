plugins { id("com.android.library") }
android {
    namespace = "org.packrag.generator"
    compileSdk = 37
    ndkVersion = "30.0.16248370"
    defaultConfig {
        minSdk = 28
        ndk { abiFilters += if(providers.gradleProperty("packragEmulatorNative").orNull=="true") listOf("arm64-v8a","x86_64") else listOf("arm64-v8a") }
        externalNativeBuild { cmake { arguments += listOf("-DANDROID_PLATFORM=android-28", "-DCMAKE_BUILD_TYPE=Release") } }
    }
    externalNativeBuild { cmake { path = file("src/main/cpp/CMakeLists.txt"); version = "3.31.1" } }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
}
dependencies {
    implementation(project(":security-crypto")); api(project(":generator-api"))
    testImplementation("junit:junit:4.13.2")
}
