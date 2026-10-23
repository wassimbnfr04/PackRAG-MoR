# M4C1 validity provenance methods

Status: C1 VERIFIED.596 Python tests,23 host methods per variant and14 real
desktop cases pass. Full development19-method gate702.381s and production-policy
14-method gate298.2s pass; all33 final JSON outputs are saved. Restoration retry
0005 passes one method/four consent checks3.749s after host transport failure0004.
Closure preflight rechecks128 runtime/424 Android inputs per variant,587 historical
identities, prior B2 saved outputs, frozen architecture and APK/native/corpus hashes.
The new physical validity method passes32/3/12 cases, maximum embedding error
9.313225746154785e-8/cosine1.0635379477097473e-7. validity-gate0001 binds acceptance.
This document records new work after B2a9ceb60. All old experiments and B2
results remain immutable. The complete v1.3 system is not accepted yet.

## Exact changes and preserved meaning

Python validity_provenance and Kotlin validityProvenance preserve the four
authenticated source/chunk boundaries and expose the effective intersection.
Start is the maximum nonnull start; exclusive end is the minimum nonnull end.
Null source boundaries are marked unknown even if a chunk supplies a known
bound. Null chunk boundaries are marked inherited even when the source side is
also unknown. No release timestamp, retrieved_at, freshness date, or current
clock is substituted for a missing source boundary. Equal/reversed effective
intersection is explicitly empty and ineligible. Individually reversed source
or chunk intervals still fail the existing signed database admission gate.

Requested jurisdiction must match the source exactly. Null source jurisdiction
does not match a supplied country; a subdivision is not silently widened to its
country. Unrequested jurisdiction imposes no new filter. Repealed/superseded
sources fail explicit current-law queries, while an interval-eligible historical
query may retain them. The specification does not reject legal_status historical,
n/a or null merely because current-law is requested. C1 keeps that exact rule;
it does not claim those metadata values establish actual legal applicability.

The filter already implemented these semantics. C1 centralizes the interval
calculation and adds explicit empty-intersection rejection/provenance; it does
not introduce a latest-document sort or authority preference. Conflict-scoped
authority and verified amendment/supersession/exception relationships remain C2.
The broader relevance/selection/language/UI obligations remain D–F.

Desktop candidates, selected records and cited canonical-source records carry
validity metadata. Android cited SourceRecord carries the same structured
values. Existing constructors remain compatible via an optional provenance
field; both actual runtime citation paths populate it. The Android source screen
will display these fields in E. C1 does not claim verified UI presentation.
Question/encoder/template/native/model/decoding parameters and canonical text
are unchanged by C1. No raw reasoning is added to reports.

## Corpus and oracle independence

product/tests/validity-cases.json, the JVM test resource and Android test asset
contain32 independently written eligibility cases and three fixed complete
provenance dictionaries. They cover inclusive starts/exclusive ends on each
level, inheritance, unknown sides, earliest/latest representable query dates,
disjoint/touching intersections, exact/unrequested/unknown/subdivision
jurisdiction, current and historical status behavior. Fixed expectations are
not computed from either implementation's eligible function.

validity-fixtures0003 contains an authenticated eight-row synthetic pack and12
retrieval scenarios. Each row has a distinct synthetic original identity and
the same exact Article-T alias. Baseline is2020–2030; superseded historical
source2010–2020; future2027–2030; narrow chunk2026–2027 within source2020–2030;
disjoint source2020–2022/chunk2023–2024; unknown source with finite2026–2027
chunk; an open French row; and an open unscoped row. All ends are exclusive.
Explicit scenario eligible sets are manually specified in the generator and
asserted before saving any reference. Multiple eligible distinct originals
produce conservative B2 ambiguity; expired/wrong-jurisdiction rows must not
manufacture it. Cases assert dense ranks are contiguous after eligibility.

Document and normalized-query vectors come from the pinned actual Granite
encoder. KDX/DB are authenticated through the unchanged importer. Stored numeric
candidate ordering/ranks/RRF/cosine references are the desktop implementation
oracle for cross-platform comparison. They are not independent semantic/legal
gold. Python adjacent tests reuse stored vectors; Android parity actually runs
Granite and requires embedding/cosine error≤1e-4 with exact candidate/rank/RRF
agreement. Graph is off, no second RRF or new ranking constant is introduced.

The pack's freshness advisory date is2020-01-01, deliberately earlier than test
queries. It must warn without overriding legal intervals. A controlled desktop
generator tests cited provenance serialization and advisory behavior; it is
explicitly not real inference. Retained actual desktop/Android LFM smoke is the
mandatory separate acceptance. Real phone smoke and production-core tests also
assert open/unknown/inherited validity survives the actual cited answer.

The corpus is SYNTHETIC/UNCALIBRATED with an ephemeral signing seed never saved.
It is not a release demonstrator, measured calibration, real legal truth, source
license review, translation review, held-out benchmark, or final gold gate.
The intermediate builder stage is not an accepted pack; only final signed
validity-boundaries.kpack and its hash-bound references enter the test assets.

## Failed attempts and limits

Fixture0001 reached a signed partial archive but failed opening a private
temporary snapshot under the Windows sandbox; cleanup was also denied.
Fixture0002 failed before signer/encoder/pack creation because Windows write_text
had produced CRLF and the retry compared against LF bytes. Corrected universal
newline text comparison preserves existing contract file bytes; hashes identify
their actual stored bytes. Fresh approved fixture0003 passes all assertions.
Both failure records remain separate, with no promoted result or relaxed filter.

device-validity0001 failed its pre-ADB test-source check because the selected
ProcessDeathDeviceTest name did not exist. It installed nothing and executed no
phone test. device-validity0002 uses the class list copied from the verified B2
manifest plus the new validity class; its result is separately versioned.

The full debug gate passes19 methods702.381s; the production-policy gate passes14
methods298.2s. All33 final JSON outputs are saved. Restoration0004 installs the
development application but fails the test-APK installation because the host ADB
daemon cannot respond/start. No consent test runs in that failed attempt. ADB
subsequently sees the same authorized phone, and fresh0005 retries unchanged
APKs. This is a host transport failure, not a model/security failure; no global
ADB restart or phone policy/radio change is made. Retry0005 subsequently passes
the consent gate and final closure preflight passes all requirements above.

APK demo remains instrumentable and Android Debug signed for policy testing.
Mobile data remains ON; app INTERNET permission must remain absent. Owner
app/model/registry contents are preserved. Functional generation timings do not
establish latency/resource acceptance, per-question memory/thermal peaks or a
causal hardware/software bottleneck. Complete C1 acceptance requires both host
variants, all regression/security/parity and actual desktop/phone gates, saved
results, development restoration and immutable source/history checks.
