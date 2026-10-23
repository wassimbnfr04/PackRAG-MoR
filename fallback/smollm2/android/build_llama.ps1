$ErrorActionPreference = 'Stop'
$rootTask = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$sdkTask = Join-Path $rootTask 'vendor/android-sdk'
$ndkTask = Join-Path $sdkTask 'ndk/30.0.16248370'
$cmakeTask = Join-Path $sdkTask 'cmake/3.31.1/bin/cmake.exe'
$ninjaTask = Join-Path $sdkTask 'cmake/3.31.1/bin/ninja.exe'
$sourceTask = Join-Path $rootTask 'vendor/llama.cpp'
$buildTask = Join-Path $rootTask 'fallback/smollm2/android/build-arm64'
& $cmakeTask -S $sourceTask -B $buildTask -G Ninja "-DCMAKE_MAKE_PROGRAM=$ninjaTask" "-DCMAKE_TOOLCHAIN_FILE=$ndkTask/build/cmake/android.toolchain.cmake" -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-28 -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_TOOLS=ON -DLLAMA_CURL=OFF -DGGML_OPENMP=OFF
if ($LASTEXITCODE -ne 0) { throw 'llama.cpp configure failed' }
& $cmakeTask --build $buildTask --target llama-cli llama-completion -j 4
if ($LASTEXITCODE -ne 0) { throw 'llama.cpp build failed' }
