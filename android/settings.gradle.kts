pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        maven { url = uri("../vendor/maven"); content { includeModule("org.jetbrains.kotlin", "kotlin-compiler-embeddable") } }
        google(); mavenCentral()
    }
}
rootProject.name = "PackRAGWeek1"
include(":week1-spike")
