pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        maven { url = uri("../../vendor/maven"); content { includeModule("org.jetbrains.kotlin", "kotlin-compiler-embeddable") } }
        google(); mavenCentral()
    }
}
rootProject.name = "PackRAGProduct"
include(":app", ":core-model", ":embedding-onnx")
include(":security-crypto", ":kpack-registry", ":retrieval")
include(":generator-llama", ":grounded-runtime")
include(":generator-api")
include(":source-viewer")
