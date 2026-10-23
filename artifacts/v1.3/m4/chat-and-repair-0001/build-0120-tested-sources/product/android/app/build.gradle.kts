plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
}
android {
    namespace = "org.packrag.product"
    compileSdk = 37
    buildToolsVersion = "37.0.0"
    ndkVersion = "30.0.16248370"
    defaultConfig {
        applicationId = "org.packrag.product"
        minSdk = 28
        targetSdk = 37
        versionCode = 1
        versionName = "1.3.0-dev"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        ndk { abiFilters += if(providers.gradleProperty("packragEmulatorNative").orNull=="true") listOf("arm64-v8a","x86_64") else listOf("arm64-v8a") }
    }
    buildFeatures { compose = true; buildConfig = true }
    buildTypes {
        getByName("debug") { buildConfigField("boolean","ALLOW_DEVELOPMENT_PACKS","true") }
        getByName("release") { buildConfigField("boolean","ALLOW_DEVELOPMENT_PACKS","false") }
        create("demo") {
            initWith(getByName("release"))
            isDebuggable = true // Instrumentation only; not final release acceptance.
            signingConfig = signingConfigs.getByName("debug")
            matchingFallbacks += "release"
            versionNameSuffix = "-policy-demo"
            buildConfigField("boolean","ALLOW_DEVELOPMENT_PACKS","false")
        }
    }
    testBuildType = providers.gradleProperty("packragTestBuildType").getOrElse("debug")
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
}
dependencies {
    implementation(project(":core-model"))
    implementation(project(":embedding-onnx"))
    implementation(project(":security-crypto"))
    implementation(project(":kpack-registry"))
    implementation(project(":retrieval"))
    implementation(project(":generator-llama"))
    implementation(project(":grounded-runtime"))
    implementation(project(":source-viewer"))
    implementation(platform("androidx.compose:compose-bom:2026.09.00"))
    implementation("androidx.compose.material3:material3")
    implementation("androidx.activity:activity-compose:1.13.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.11.0")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.11.0")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.3.0")
    androidTestImplementation("androidx.test:runner:1.7.0")
    androidTestImplementation("androidx.sqlite:sqlite-bundled:2.7.1")
    androidTestImplementation(platform("androidx.compose:compose-bom:2026.09.00"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
}
