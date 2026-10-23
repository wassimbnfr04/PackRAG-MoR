$ErrorActionPreference = 'Stop'
$rootTask = Split-Path -Parent $PSScriptRoot
$pathsTask = Get-Content (Join-Path $rootTask 'artifacts/week1/environment/android_tool_paths.json') -Raw | ConvertFrom-Json
$env:JAVA_HOME = $pathsTask.jdk
$env:GRADLE_USER_HOME = Join-Path $rootTask '.cache/gradle'
$env:ANDROID_USER_HOME = Join-Path $rootTask '.cache/android'
$env:ANDROID_HOME = $pathsTask.sdk
$sdkPathTask = $pathsTask.sdk.Replace('\','/')
Set-Content -LiteralPath (Join-Path $rootTask 'android/local.properties') -Value "sdk.dir=$sdkPathTask"
& $pathsTask.gradle -p (Join-Path $rootTask 'android') --no-daemon :week1-spike:testDebugUnitTest :week1-spike:assembleDebug :week1-spike:assembleDebugAndroidTest
if ($LASTEXITCODE -ne 0) { throw 'Android build/tests failed; preserve logs' }
