# Install or build PackRAG through M4

The source publication left dependency restoration too manual. The distribution
repair adds the tested development APK, signed repair fixture, small setup bundle,
pinned llama.cpp submodule, Gradle wrapper, asset/tool installers and a build
launcher independent of the original workstation inventory. App behavior remains
the accepted evidence-only M4 implementation.

## A. Run the APK without compiling

Download the files from [M4 development distribution](https://github.com/wassimbnfr04/PackRAG-MoR/releases/tag/m4-distribution-v1):

- `PackRAG-M4-development.apk`: exact tested build0120, ARM64 and x86-64.
- `PackRAG-M4-repair-test.kpack`: approved signed development repair fixture.
- `PackRAG-M4-setup.zip`: runtime setup scripts, configuration and exact pins.
- `SHA256SUMS.txt`, `ARTIFACT_PROVENANCE.json`, `DOWNLOAD_AND_INSTALL.md`.

Put them in one folder. You need Python3.12 and an authorized USB-debugging phone.
You do **not** need JDK/NDK/Gradle/llama.cpp or a private signing key for this route.

```powershell
Expand-Archive -LiteralPath .\PackRAG-M4-setup.zip -DestinationPath .
py -3.12 scripts/bootstrap_packrag.py assets --download
py -3.12 scripts/bootstrap_packrag.py tools --adb-only --download
$Adb = (Resolve-Path .\vendor\android-sdk\platform-tools\adb.exe).Path
& $Adb devices -l
$Device = 'REPLACE_WITH_AUTHORIZED_SERIAL'
& $Adb -s $Device install -r .\PackRAG-M4-development.apk
$RunTag = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,6)
py -3.12 -m scripts.v13_install_phone_assets --adb $Adb --serial $Device `
    --include-generator --run "artifacts/local-runs/$RunTag-assets"
& $Adb -s $Device push .\PackRAG-M4-repair-test.kpack /sdcard/Download/PackRAG-M4-repair-test.kpack
& $Adb -s $Device shell am start -n 'org.packrag.product/.MainActivity'
```

Unlock the phone and approve USB debugging. The asset helper uses binary-safe
ADB transport, full hashes and staged installation under the app UID; no root.
Existing mismatched files are refused rather than silently replaced. Use the
app's Local assets import screen to explicitly replace them with correct files.

In the app, open **Local model & files → Check local files**; verify all four
slots. Then **Import signed knowledge pack**, choose the KPack from Downloads
and check the active identity. Ask:

> How should I remove and reconnect the Framework Laptop 12 fan connector without damaging its socket?

Open the cited source. The fixture contains short documented test digests, not
final owner packs or complete original manuals. General chat without a pack is
future work. Once setup finishes, on-phone answers require neither USB nor a
host server. Mobile data can stay on; radio-isolated benchmarking is not claimed.

### Model files

Runtime assets total about **2.01GB**, plus about8MB for ADB. Downloads occur only
with `--download`. `product/config/asset-downloads.json` specifies immutable
upstream revisions, exact filenames, sizes and SHA256 values. Only the ONNX
inference model is acquired, not unnecessary Granite training weights. The
small official template and license are included in source/setup material.

To reuse an existing provisioned project:

```powershell
py -3.12 scripts/bootstrap_packrag.py assets --from-root 'PATH_TO_EXISTING_PROJECT'
```

Add `--download` to acquire only missing source assets. Add `--verify-only` to
check without copying; its output distinguishes source verification from local
installation. Model license terms still apply; weights are acquired separately
rather than publicly rehosted in the source repository or APK.

## B. Build from source

Install Git and Python3.12, then:

```powershell
git clone --recurse-submodules https://github.com/wassimbnfr04/PackRAG-MoR.git
Set-Location PackRAG-MoR
py -3.12 scripts/bootstrap_packrag.py native
```

For an existing plain clone:

```powershell
py -3.12 scripts/bootstrap_packrag.py native --install
```

The real submodule at `vendor/llama.cpp` pins commit
`19e28a27702117d8f2eb16b825b9a308111f67d9`. Bootstrap verifies its commit and clean
status. GitHub's source ZIP omits submodule contents; clone recursively or initialize
it explicitly rather than expecting an upstream checkout inside the ZIP.

### Windows x64 tools

```powershell
py -3.12 scripts/bootstrap_packrag.py tools --download
```

This installs the recorded Microsoft JDK17 and Google CLI/platform/build-tools37,
NDK30.0.16248370, CMake3.31.1 and ADB using exact checksummed archives and checked
extraction paths. Installed tools remain ignored dependencies, not Git payloads.
It writes this clone's ignored `.packrag.local.json` and `local.properties`.
The build tools can require over1GB of downloads and are unnecessary for routeA.

Review and accept Android SDK licenses:

```powershell
& .\vendor\android-sdk\cmdline-tools\latest\bin\sdkmanager.bat `
    --sdk_root=vendor/android-sdk --licenses
```

Follow the pinned CLI's actual license prompt; the installer does not silently
accept licenses. If tools already exist, skip downloads and configure their paths:

```powershell
py -3.12 scripts/bootstrap_packrag.py configure `
    --sdk 'PATH_TO_ANDROID_SDK' --java-home 'PATH_TO_JDK17'
```

macOS/Linux use their own JDK17/SDK installations and checked-in Unix `gradlew`;
the archive installer and PowerShell build route are validated on Windows x64.

### Build with the wrapper

The exact tokenizer is needed by the host parity test, even for an APK build
that does not bundle weights. Acquire only the roughly25MB build-test assets:

```powershell
py -3.12 scripts/bootstrap_packrag.py assets --build-only --download
$RunTag = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,6)
& .\scripts\build_android_portable.ps1 `
    -RunDirectory "artifacts/local-runs/$RunTag-build" -Variant debug
```

The launcher uses `product/android/gradlew.bat`, never the old machine inventory.
The wrapper downloads exact Gradle9.6.0 and checks its published SHA256; no global
Gradle install is needed. The first build resolves pinned Maven dependencies.
Use `-Offline` only after all distributions/dependencies are cached. Add
`-EmulatorNative` for debug ARM64+x86-64; default is ARM64. Host tests, source
identities, logs and generated APKs are captured in the fresh output directory.

Gradle generates your local debug signing keystore automatically. A different
certificate cannot update an existing APK in place; preserve app data and plan
signing continuity before replacing an installed build.

The release APK is the original physically tested M4 artifact. A newly compiled
native library is not automatically that same byte identity. Current
`LlamaGenerator` native SHA constants describe the accepted build rather than an
in-process hash measurement. Inspect actual rebuilt libraries and capture new
build identities before claiming new acceptance. Never label a new compilation
as the original tested APK without comparing its bytes.

## C. Keys and snapshot boundaries

Installing the APK, loading models, verifying a pack and asking questions require
no private signing key. The publisher's private seed is needed only to sign new
packs as that existing publisher. A new publisher generates its own private key
and explicitly configures its public trust in its app. The existing setup rejects
silent key rotation. See [signing identities](SIGNING_IDENTITIES.md).

`m4-baseline` preserves the initial cumulative source snapshot.
`m4-distribution-v1` adds the distribution/setup repair, without new app policies.
The old snapshot verifier is meant for the old tag's checkout, not a claim that
later setup additions are byte-identical to the initial publication.

## D. Existing M4 host backend

The release also supplies `PackRAG-M4-host-linux-x86_64.zip`, containing the exact
hash-pinned Linux llama-server used by the M4 desktop path and its upstream
license. Extract it at the source repository root. In Linux/WSL make
`04_LFM25_26B_Candidate_Evidence/runtime/wsl-build/bin/llama-server` executable and
check its normal Linux libraries with `ldd`. This is Linux x86-64, not a native
Windows/ARM executable. Models and Python dependencies remain separately needed.

The existing M4 launcher expects a working `kali-linux` WSL distribution:

```powershell
wsl.exe -d kali-linux --exec /bin/true
py -3.12 -m venv .venv-pack
& .\.venv-pack\Scripts\python.exe -m pip install -r requirements-pack.txt
& .\.venv-pack\Scripts\python.exe -X utf8 -m scripts.v13_smoke `
    --run "artifacts/local-runs/$RunTag-host-smoke"
```

Use a new environment/output directory only when needed; do not overwrite existing
ones. This is the original baseline2048/512 smoke, not the app's quoted profile
or a new expertise benchmark. The release runtime hash matches the M4 desktop
lock; its distribution does not claim a new successful WSL run on this machine.
WSL virtualization availability must be resolved independently of model quality.
