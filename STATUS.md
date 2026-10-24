# PackRAG implementation through M4

## 24 October: distribution/setup repair

The cumulative M0–M4 app behavior is retained. New setup changes add the exact
llama.cpp submodule, official checksum-pinned Gradle wrapper, standard-library
model/tool acquisition, portable SDK/JDK configuration/build launcher and ADB
override support. The development release supplies the original tested M4 APK,
approved signed repair fixture, small setup ZIP and exact Linux host runtime.
Models remain verified external downloads; private signing custody stays private.

Validation:1071 Python tests passed (the1054 baseline plus17bootstrap tests);
portable wrapper build passed99Android host tests and assembled APKs. Real small
download/ADB extraction/model hash checks and original APK signature passed.
The new compilation's native bytes differ, so the release retains original
tested build0120 rather than claiming fresh physical acceptance. See
docs/publication/DISTRIBUTION_VERIFICATION.json and docs/GETTING_STARTED_M4.md.
The immutable m4-baseline tag retains the initial source publication.

Publication baseline prepared23October2026 from the verified cumulative
checkpoint8f0ccaa5cfac125c2ec2adf291cef3d1d7d4c3b0. This includes the whole
project implementation achieved through M0–M4, not only the M4 diff.

M0–M4 functional gates: accepted within their recorded development scope.
M5–M8/final release acceptance: pending. General chat without a pack and
pack-agnostic policy revision: future work, not implemented in this baseline.

Current source: product/android and product/packrag. Retained earlier components
and evidence remain in their original relative paths for reproducibility.
The original checkpoint STATUS is preserved under
docs/publication/original-checkpoint-docs/STATUS.md. See README.md and
docs/publication/README.md for the publication boundaries and verification.

Fresh publication-copy Python regression:1054 passed,0failures/errors/skips.
All640 recorded Android build inputs,176 Kotlin and3 Java files match the
accepted source hashes. No new Android build, phone or emulator acceptance is
claimed. Post-M4 working-tree code/experiments are outside this snapshot.
