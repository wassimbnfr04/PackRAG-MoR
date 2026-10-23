# ADR-008: explicit native x86 emulator acceptance build

Status: accepted scoped implementation direction; device validation pending. 2026-10-12.

Owner explicitly requested emulator use where possible. The existing ARM-only JNI ran through libndk_translation and failed to complete one answer within900s. The Samsung is disconnected. The owned API36 emulator exposes x86_64, two CPUs and AVX/AVX2/FMA/F16C; existing NDK30 already includes its compiler. No new download or runtime/model library is required.

Add an explicit debug-only build-script opt-in for arm64-v8a plus x86_64. Default builds and demo/release remain ARM-only; do not change the v1.3 production ABI. Both variants compile the same pinned llama.cpp/C++ API and known baseline/quote context policy. Report the actual compiled ABI from JNI and pin each actual packaged library SHA independently; never label x86 bytes or performance as Samsung/ARM. A bootstrap build with placeholder pins is not installable acceptance evidence: capture actual bytes, update pins, rebuild and verify before any device launch.

The emulator may establish actual local Android model/decoder/ownership/UI functionality and serialization contracts. ARM compilation is not physical ARM execution; required final phone/resource/thermal acceptance remains physical. Do not infer phone peak memory, throughput or bottlenecks from emulator observations. Preserve the failed ARM-bridge original. The build-script opt-in rejects demo variant; actual artifact command/ABI/pins/source hashes and explicit environment accompany each test.
