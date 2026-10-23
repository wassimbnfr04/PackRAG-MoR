param([Parameter(Mandatory=$true)][string]$RunDirectory, [switch]$Offline, [ValidateSet('debug','demo')][string]$Variant='debug',[switch]$EmulatorNative)
$ErrorActionPreference = 'Stop'
if ($EmulatorNative -and $Variant -ne 'debug') { throw 'Emulator ABI opt-in is for the debug acceptance build only' }
$rootTask = Split-Path -Parent $PSScriptRoot
$runTask = [IO.Path]::GetFullPath((Join-Path $rootTask $RunDirectory))
if (-not $runTask.StartsWith($rootTask + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Run output must be inside this workspace' }
if (Test-Path -LiteralPath $runTask) { throw 'Choose a new versioned build directory' }
New-Item -ItemType Directory -Path $runTask | Out-Null
$pathsTask = Get-Content -LiteralPath (Join-Path $rootTask 'artifacts/week1/environment/android_tool_paths.json') -Raw | ConvertFrom-Json
$env:JAVA_HOME = $pathsTask.jdk
$env:GRADLE_USER_HOME = Join-Path $rootTask '.cache/gradle'
$env:ANDROID_USER_HOME = Join-Path $rootTask '.cache/android'
$env:ANDROID_HOME = $pathsTask.sdk
$env:PATH = $env:JAVA_HOME + '\bin;' + $env:PATH
$projectTask = Join-Path $rootTask 'product/android'
& (Join-Path $rootTask '.venv-pack/Scripts/python.exe') -X utf8 -m scripts.v13_android_source_identity --output (Join-Path $runTask 'source-at-build-start.json')
if ($LASTEXITCODE -ne 0) { throw 'Source identity capture failed' }
Set-Content -LiteralPath (Join-Path $projectTask 'local.properties') -Value ('sdk.dir=' + $pathsTask.sdk.Replace('\','/'))
$unitTask = if ($Variant -eq 'debug') { 'testDebugUnitTest' } else { 'testReleaseUnitTest' }
$suffixTask = if ($Variant -eq 'debug') { 'Debug' } else { 'Demo' }
$argumentsTask = @('-p', $projectTask, '--no-daemon', '--console=plain', '--max-workers=4', $unitTask, (':app:assemble'+$suffixTask), (':app:assemble'+$suffixTask+'AndroidTest'), ('-PpackragTestBuildType='+$Variant))
if ($Offline) { $argumentsTask += '--offline' }
if ($EmulatorNative) { $argumentsTask += '-PpackragEmulatorNative=true' }
& $pathsTask.gradle @argumentsTask 2>&1 | Tee-Object -FilePath (Join-Path $runTask 'gradle.log')
$exitTask = $LASTEXITCODE
@{ exit_code=$exitTask; variant=$Variant; instrumentation_debuggable=$true; final_release_acceptance=$false; arguments=$argumentsTask; tool_paths=$pathsTask; status=$(if ($exitTask -eq 0) {'BUILD_AND_HOST_TESTS_PASS_NOT_DEVICE_ACCEPTANCE'} else {'FAIL'}) } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $runTask 'build-result.json') -Encoding utf8
if ($exitTask -eq 0) {
    foreach ($apkRootTask in @(('app/build/outputs/apk/'+$Variant), ('app/build/outputs/apk/androidTest/'+$Variant))) {
        foreach ($itemTask in Get-ChildItem -LiteralPath (Join-Path $projectTask $apkRootTask) -File -Filter '*.apk') {
            Copy-Item -LiteralPath $itemTask.FullName -Destination (Join-Path $runTask $itemTask.Name)
        }
    }
}
$testCountTask = 0
foreach ($moduleTask in Get-ChildItem -LiteralPath $projectTask -Directory) {
    $testRootTask = Join-Path $moduleTask.FullName ('build/test-results/'+$unitTask)
    if (Test-Path -LiteralPath $testRootTask) {
        foreach ($xmlTask in Get-ChildItem -LiteralPath $testRootTask -File -Filter 'TEST-*.xml') {
            $destinationTask = Join-Path $runTask ('host-tests/' + $moduleTask.Name)
            New-Item -ItemType Directory -Path $destinationTask -Force | Out-Null
            Copy-Item -LiteralPath $xmlTask.FullName -Destination (Join-Path $destinationTask $xmlTask.Name)
            [xml]$suiteTask = Get-Content -LiteralPath $xmlTask.FullName -Raw
            $testCountTask += [int]$suiteTask.testsuite.tests
        }
    }
}
@{ test_methods=$testCountTask; status=$(if ($exitTask -ne 0) {'FAILED_BUILD_OR_TESTS_SEE_XML_AND_LOG'} elseif ($testCountTask -gt 0) {'HOST_TEST_METHODS_PASSED'} else {'NO_HOST_TEST_METHODS_EXIST'}); note='Inspect each XML for fixture/case counts; build-only success is not milestone completion. XML for unchanged modules may be from an UP-TO-DATE task; log records task execution.' } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runTask 'host-test-summary.json') -Encoding utf8
if ($exitTask -ne 0) { throw 'Android milestone build failed; stop progression and inspect the versioned log' }
