# M4 distribution repair — 24 October 2026

The original cumulative source publication omitted a ready APK and left upstream
source/tool/model restoration manual. The implementation files were present, but
that was not sufficient for someone to clone and run the system conveniently.

The correction adds:

- An original physically tested M4 development APK, signed repair fixture,
  checksums, provenance, install guide and small standard-library setup ZIP as
  GitHub release assets. The APK is build0120, not a newly accepted rebuild.
- Optional exact pinned Linux x86-64 host llama-server and upstream license.
- A real llama.cpp Git submodule at the exact pinned commit.
- Official generated Unix/Windows Gradle wrapper files, wrapper JAR and published
  Gradle9.6.0 distribution checksum.
- Standard-library model/config acquisition with immutable upstream revisions,
  size/SHA verification, explicit downloads, local-copy/verify-only modes and no
  silent overwrite of wrong existing files. Build-only mode needs about25MB,
  while full runtime acquisition is about2.01GB.
- Pinned Windows JDK/SDK/NDK/CMake/ADB archive installation and local SDK/JDK
  configuration; a portable launcher using this clone's configuration and wrapper
  instead of old absolute workstation inventory paths.
- ADB discovery/override support in the existing binary-safe asset helper and
  clear separation of APK, publisher and intentionally public test signing keys.

No M5 feature, general-chat policy, retrieval threshold or model weight changes
are introduced. Existing public publisher trust and app/native policy are retained.
Model weights and actual private signing custody are not publicly rehosted.

Verification is recorded in `DISTRIBUTION_VERIFICATION.json`. It distinguishes
the new package/build checks from the original physical-device acceptance.
The initial portable build failed on its missing tokenizer parity input; that
failure is preserved. Build-only acquisition plus early preflight repaired the
setup, and the next build passed99host tests and produced APKs.

The newly built ARM library differs from the original accepted byte hash. It is
not substituted for the release's tested artifact, and existing native-identity
constants are not weakened or silently rewritten. Source-build success alone
does not establish new physical-device acceptance. The verified development APK
and its original library hashes are retained in M4_DEVELOPMENT_APK.json.
