# Getting started with the M4 source baseline

This is the accepted M4 implementation, not the later free-answer host pilot.
The Android app requires an active verified pack. This source publication is not
a portable turnkey installer; final bootstrap/release acceptance is future work.

## Prerequisites

- Python3.12 and packages listed in `requirements-pack.txt`. This is a direct
  dependency list, not a complete transitive environment lock.
- Exact LFM2.5 QAD-Q4_0 GGUF at the repository root and its official chat template
  at `04_LFM25_26B_Candidate_Evidence/model/chat_template.jinja`.
- The complete pinned Granite asset directory at `models/v1.3/granite`.
- For Android builds: the JDK/Gradle/SDK/NDK/CMake versions recorded in
  `product/config/toolchain.lock.json`.
- For desktop generation: the pinned Linux CPU llama.cpp binary and a working
  `kali-linux` WSL environment for the existing M4 launcher.

The four main Android assets are the GGUF, template, Granite tokenizer JSON and
Granite ONNX model; they total about2.01GB. They are not packaged in an APK or
knowledge pack. Restore them from their approved original sources and verify the
exact lockfile hashes. A public source checkout deliberately does not contain
weights, a private publisher seed, SDK downloads or the original workstation's
Python environment. Acquiring dependencies can involve substantial downloads.

The later native Windows research server and21October host example are not part
of this M4 snapshot. Do not run commands for those later experiments and assume
their files are included here.

## Restore the upstream native source for an Android build

Run from the repository root, using an unused destination:

```powershell
git clone https://github.com/ggml-org/llama.cpp.git vendor/llama.cpp
git -C vendor/llama.cpp checkout --detach 19e28a27702117d8f2eb16b825b9a308111f67d9
git -C vendor/llama.cpp status --short
```

The source must be at the exact pinned commit with no local modifications. Do not
overwrite an existing vendor checkout or weaken its identity guard. External
native libraries are separately SHA-pinned; a fresh compiler/toolchain can produce
different bytes. The identity guard is intentional and needs explicit review of
a new binary, not silent hash replacement.

## Python tests

With a suitable environment and restored Python dependencies:

```powershell
py -3.12 -m venv .venv-pack
& .\.venv-pack\Scripts\python.exe -m pip install -r requirements-pack.txt
$RunTag = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Path "artifacts/local-runs/$RunTag" | Out-Null
& .\.venv-pack\Scripts\python.exe -X utf8 -m pytest tests product/tests -q `
    -p no:cacheprovider `
    --basetemp "artifacts/local-runs/$RunTag/temp" `
    --junitxml "artifacts/local-runs/$RunTag/pytest.xml"
```

Create the environment only if it does not already exist. Most unit/fixture tests
do not require actual model weights. Model-backed smoke and device tests require
their declared assets. New results go under ignored `artifacts/local-runs`, not
the original historical result directories.

## Android build on the original provisioned workstation

```powershell
$RunTag = Get-Date -Format 'yyyyMMdd-HHmmss'
& .\scripts\v13_build_android.ps1 `
    -RunDirectory "artifacts/local-runs/$RunTag-android" -Offline -Variant debug
```

For a native x86-64 emulator debug build, add `-EmulatorNative`. Default builds
are ARM64; demo does not enable development packs and rejects that ABI flag.

The existing build helper reads the preserved tool inventory at
`artifacts/week1/environment/android_tool_paths.json`. It contains the original
workstation paths. On a different workstation, use a separate local inventory/
build invocation with the new paths instead of rewriting historical records.
Set session `JAVA_HOME`, `ANDROID_HOME`, `ANDROID_USER_HOME`, `GRADLE_USER_HOME`
and the checkout's `product/android/local.properties` as needed. The Android
project uses installed Gradle; a Gradle wrapper is not included. Offline builds
need the exact cached dependencies, including the recorded Kotlin mirror.

See `docs/v1.3/M4_REPRODUCTION_AND_ACCEPTANCE.md` for tool/source/native pin and
acceptance boundaries. A fresh signed nondebug release/portable bootstrap is not
claimed by an accepted development build.

## Install and run on Android

Use your actual APK path and device serial:

```powershell
$Adb = '.\vendor\platform-tools\adb.exe'
& $Adb devices -l
$Device = 'REPLACE_WITH_AUTHORIZED_SERIAL'
& $Adb -s $Device install -r 'PATH_TO_YOUR/app-debug.apk'
& .\.venv-pack\Scripts\python.exe -X utf8 -m scripts.v13_install_phone_assets `
    --serial $Device --include-generator `
    --run "artifacts/local-runs/$RunTag-assets"
& $Adb -s $Device shell am start -n 'org.packrag.product/.MainActivity'
```

No APK is committed in this source snapshot. The asset helper uses binary-safe
`adb exec-in`, app-UID `run-as`, full hashes and staged rename. It requires a
debuggable installed app and refuses silently replacing mismatched assets.
Alternatively use the app's **Local model & files** screen to import each exact
file through the system picker, then check all four slots.

Transfer an approved signed test `.kpack` to Downloads, import it with the app's
**Import signed knowledge pack** menu, and verify the active identity. ADB push
alone does not activate a pack. Existing signed fixtures may be used with their
documented scope; creating new approved packs needs separately held publisher
custody. The intentionally public test seed is not that publisher key.

For an emulator, use API28+ and an APK containing native x86-64 JNI, sufficient
RAM/storage and functioning CPU virtualization. A copied source tree contains no
AVD image or preconfigured emulator. The Android app runs its own local encoder
and generator; it does not require a desktop server or `adb reverse`. Emulator
functionality does not establish physical-phone speed or thermal acceptance.

Once assets and the active pack are installed, USB is not needed for ordinary
on-phone inference. The app has no INTERNET permission; mobile data can stay on.

## Desktop M4 smoke

The existing launcher owns a pinned local Linux server, builds a new development
pack and runs its historical bounded smoke. With the exact model/template/binary,
Granite assets and working `kali-linux` WSL installed:

```powershell
& .\.venv-pack\Scripts\python.exe -X utf8 -m scripts.v13_smoke `
    --run "artifacts/local-runs/$RunTag-desktop-smoke"
```

This launcher uses the typed2048/512 baseline, not the app's explicitly selected
3072/1536 quotation policy. It is not a benchmark of the final app profile.
Do not label a failed WSL startup as a model failure. For current-policy desktop
reproduction, follow the retained M4 quoted-runtime collectors and select fresh
run paths; their source/APK/fixture bindings must still be checked. Do not rerun
a dated collector into its original output directory.
