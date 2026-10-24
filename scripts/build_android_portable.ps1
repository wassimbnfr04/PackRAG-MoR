param(
    [Parameter(Mandatory=$true)][string]$RunDirectory,
    [string]$AndroidSdk,
    [string]$JavaHome,
    [string]$Python,
    [string]$GradleUserHome,
    [switch]$Offline,
    [switch]$EmulatorNative,
    [ValidateSet('debug','demo')][string]$Variant='debug'
)
$ErrorActionPreference = 'Stop'
$rootTask = Split-Path -Parent $PSScriptRoot
$configTask = Join-Path $rootTask '.packrag.local.json'
$localTask = if (Test-Path -LiteralPath $configTask) { Get-Content -LiteralPath $configTask -Raw | ConvertFrom-Json } else { $null }
if (-not $AndroidSdk) { $AndroidSdk = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } elseif ($localTask) { $localTask.sdk } else { $env:ANDROID_SDK_ROOT } }
if (-not $JavaHome) { $JavaHome = if ($env:JAVA_HOME) { $env:JAVA_HOME } elseif ($localTask) { $localTask.jdk } else { $null } }
if (-not $Python) { $Python = if (Test-Path -LiteralPath (Join-Path $rootTask '.venv-pack/Scripts/python.exe')) { Join-Path $rootTask '.venv-pack/Scripts/python.exe' } elseif ($localTask) { $localTask.python } else { (Get-Command python -ErrorAction Stop).Source } }
if (-not $GradleUserHome) { $GradleUserHome = if ($localTask) { $localTask.gradle_user_home } else { Join-Path $rootTask '.cache/gradle' } }
if (-not $AndroidSdk -or -not $JavaHome) { throw 'Configure this clone with python scripts/bootstrap_packrag.py configure --sdk SDK_PATH --java-home JDK17_PATH' }
if ($EmulatorNative -and $Variant -ne 'debug') { throw 'Emulator native opt-in is debug only' }
$runTask = [IO.Path]::GetFullPath((Join-Path $rootTask $RunDirectory))
if (-not $runTask.StartsWith($rootTask + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Run path must stay inside this checkout' }
if (Test-Path -LiteralPath $runTask) { throw 'Choose a new output directory' }
New-Item -ItemType Directory -Path $runTask | Out-Null
$env:JAVA_HOME = [IO.Path]::GetFullPath($JavaHome)
$env:ANDROID_HOME = [IO.Path]::GetFullPath($AndroidSdk)
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
$env:GRADLE_USER_HOME = [IO.Path]::GetFullPath($GradleUserHome)
$env:ANDROID_USER_HOME = Join-Path $rootTask '.cache/android-portable'
$env:PATH = (Join-Path $env:JAVA_HOME 'bin') + ';' + $env:PATH
$projectTask = Join-Path $rootTask 'product/android'
Set-Content -LiteralPath (Join-Path $projectTask 'local.properties') -Value ('sdk.dir=' + $env:ANDROID_HOME.Replace('\','/')) -Encoding utf8
Push-Location -LiteralPath $rootTask
try {
    & $Python -X utf8 (Join-Path $rootTask 'scripts/bootstrap_packrag.py') assets --build-only --verify-only
    if ($LASTEXITCODE -ne 0) { throw 'Build-test assets missing. Run python scripts/bootstrap_packrag.py assets --build-only --download first.' }
    & $Python -X utf8 -m scripts.v13_android_source_identity --output (Join-Path $runTask 'source-at-build-start.json')
    if ($LASTEXITCODE -ne 0) { throw 'Source/native identity verification failed' }
    $unitTask = if ($Variant -eq 'debug') { 'testDebugUnitTest' } else { 'testReleaseUnitTest' }
    $suffixTask = if ($Variant -eq 'debug') { 'Debug' } else { 'Demo' }
    $argumentsTask = @('-p',$projectTask,'--no-daemon','--console=plain','--max-workers=4',$unitTask,(':app:assemble'+$suffixTask),(':app:assemble'+$suffixTask+'AndroidTest'),('-PpackragTestBuildType='+$Variant))
    if ($Offline) { $argumentsTask += '--offline' }
    if ($EmulatorNative) { $argumentsTask += '-PpackragEmulatorNative=true' }
    & (Join-Path $projectTask 'gradlew.bat') @argumentsTask 2>&1 | Tee-Object -FilePath (Join-Path $runTask 'gradle.log')
    $exitTask = $LASTEXITCODE
    @{exit_code=$exitTask;variant=$Variant;arguments=$argumentsTask;sdk=$env:ANDROID_HOME;jdk=$env:JAVA_HOME;status=$(if ($exitTask -eq 0) {'BUILD_AND_HOST_TESTS_PASS_NOT_DEVICE_ACCEPTANCE'} else {'FAIL'})} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $runTask 'build-result.json') -Encoding utf8
    if ($exitTask -ne 0) { throw 'Build failed; inspect the new run log' }
    foreach ($directoryTask in @((Join-Path $projectTask ('app/build/outputs/apk/'+$Variant)),(Join-Path $projectTask ('app/build/outputs/apk/androidTest/'+$Variant)))) {
        Get-ChildItem -LiteralPath $directoryTask -Filter '*.apk' -File | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $runTask $_.Name) }
    }
} finally { Pop-Location }
