# Pinned query Unicode methods and interpretation

Status: B1 VERIFIED. Debug phone gate passes 16 methods in 538.278s; production
policy gate passes 12 methods in 324.387s; final development restoration passes
four copy/consent checks in one method in 3.539s. All 29 structured outputs are
saved. unicode-gate0001 records final acceptance and immutable document
snapshots. B2, full M4 and release packs remain incomplete.

## Why this change exists

query-audit0001 compiled no probe and establishes no normalization result.
Java processes Unicode escapes before source lexing; the harness had inserted
control escapes into its regular-expression source. query-audit0002 uses
escaped regex source and records ten inputs and the pinned JDK output. One
differs from Python15: U+1E030 NFKC maps to Cyrillic U+0430 in Python but remains
U+1E030 in JDK17. JDK17 Character documents Unicode13 support. The new phone
method observes Android's built-in NFKC maps this character correctly; no
phone-version failure is inferred from a desktop-JDK mismatch.

## Exact implementation

The existing sequence remains NFKC → remove tatweel U+0640 and Arabic marks
U+064B–065F/U+0670 → default Unicode lowercase → collapse recognized whitespace
to ASCII space and remove leading/trailing space. It transforms a retrieval
copy; canonical source records, raw user input, IDs and archive folding are
unchanged. B1 does not change embedding inputs or regex word extraction; those
are explicitly audited in B2. Model, template, native code, decoding and thread
settings are unchanged.

scripts/v13_query_unicode.py requires Python UCD15 and checks the acquired raw
file hashes. It generates a 176,591-byte JSON table (SHA256
3fa30da03423d95c0d9943c401d61a105969a55ec62a2c8432e2659a5f31e557) and
a 286,941-byte Kotlin table (SHA256
c1a29f068c08b1e6392dcab98b5e928055dbaf6c031da59320878664b542b550).
There are 5,857 full compatibility decompositions excluding algorithmic Hangul,
922 nonzero combining classes, 941 eligible composition pairs and 1,433 full
single-character lowercase mappings. Official DerivedCoreProperties supplies
Cased/Case_Ignorable context. Word and whitespace ranges derive from pinned
Python15 categories; word tables are prepared, not wired into B1 retrieval.

Both implementations fully decompose, stably order each combining run (including
leading marks), compose without crossing canonical blocking, and implement
Hangul L/V/T algorithmically. Successful composition does not update the
preceding combining class. Default lowercase handles Greek Final_Sigma by
looking for preceding/following Cased scalars while ignoring Case_Ignorable.
Conditional Turkish/Lithuanian locale tailoring is not selected. The generated
Kotlin map functions are split to avoid JVM method-size limits and require no
Android JSON parser or context dependency.

## Independent and dependent checks

Official Unicode15 NormalizationTest.txt is an external expected-result corpus,
copied byte-identically to host and device tests with source hashes verified.
All 19,074 rows compare NFKC of each of five columns to column 4: 95,370 comparisons
per platform. They cover canonical ordering/composition, compatibility and
Hangul interactions beyond isolated characters.

The Python scalar check covers 1,112,064 valid scalar values, excluding 2,048
surrogates, comparing frozen NFKC/lowercase against pinned Python15. This check
shares the generator's Python oracle; it is not independently sufficient alone.
Official UnicodeData separately checks category/combining/decomposition fields.
Deterministic regeneration compares both generated files byte for byte.
Special-case context tests and all 1,433 nonidentity lowercase characters make
1,453 shared raw/normalized cases. This is exhaustive for isolated lowercase
changes, not for every possible string, script context or OS built-in result.
Malformed-surrogate query rejection remains B2.

The new Android method records table identity, case outputs, official counts
and one OS-normalizer observation. Its observed JSON is saved during the
combined run; that observation alone does not establish aggregate acceptance.
Both combined runs subsequently pass, as recorded above. Full
retained gates cover adjacent authenticated DB alias validation, FTS/dense/RRF,
prompt tokens, cancellation/recovery, raw-buffer handling and actual LFM answer
to canonical citation. Synthetic development data never establishes calibration,
source truth, real translation review or held-out accuracy.

## Evidence boundaries and preservation

Python run0002 has 501 PASS and 587 unchanged historical identities. Both
builds0003/0004 have 21 passing host methods. Desktop smoke0002 passes 14 actual
cases with owned-server cleanup. Source-at-build-start captures 403 Android
inputs per variant; the desktop manifest captures 116 public runtime/config/test
inputs. Live PLAN/STATUS evolve after Python manifest capture and are excluded
from claims of unchanged runtime source, while their original captured hashes
remain intact. The final closure rechecks every captured runtime input, all
587 historical identities, and both packaged test-corpus hashes against official
bytes. The generic build-start collector includes every public Android source
and asset file, including the TXT corpus; the extra packaged-byte checks verify
that the assembled test APKs contain those same bytes too. The initial closure
snapshot incorrectly described TXT capture; CORRECTION.md in unicode-gate0001
records this documentation-only correction without changing frozen results.

APK inspection0002 failed after a wrong guessed native-entry name; the failed
directory is preserved. Inspection0003 uses observed libpackrag_jni.so and
passes no-INTERNET/public-store/no-fixture-custody-entry checks with unchanged
JNI SHA361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef.
This instrumentable Android-Debug-signed demo is not a final release.

Raw Unicode files and acquisition manifest remain immutable. The license
available at acquisition accompanies generated tables in product/licenses;
final Android product legal notices are completed with M4E. No weights or
private publisher seeds are downloaded/copied into evidence. Phone mobile data
stays ON, so no airplane/radio-isolation acceptance is claimed. No phone
privilege/governor/affinity/thermal setting is changed. Functional gate timings
are not resource/performance acceptance or a causal bottleneck diagnosis.

Primary references: [Unicode15 data](https://www.unicode.org/Public/15.0.0/ucd/),
[JDK17 Character](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/Character.html),
[Unicode license](https://www.unicode.org/license.txt).
