plugins { id("com.android.library") }
android {
    namespace = "org.packrag.retrieval"
    compileSdk = 37
    defaultConfig { minSdk = 28 }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
}
dependencies {
    implementation(project(":core-model"))
    implementation(project(":kpack-registry"))
    testImplementation("junit:junit:4.13.2")
}
