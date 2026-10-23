plugins { id("com.android.library") }
android {
    namespace = "org.packrag.runtime"
    compileSdk = 37
    defaultConfig { minSdk = 28 }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
}
dependencies {
    implementation(project(":core-model"))
    implementation(project(":embedding-onnx"))
    implementation(project(":security-crypto"))
    implementation(project(":kpack-registry"))
    implementation(project(":retrieval"))
    implementation(project(":generator-api"))
    testImplementation("junit:junit:4.13.2")
}
