# Build-input scope clarification

The immutable closure-time M4B1_UNICODE_METHODS.md snapshot incorrectly states
that the generic build-start collector excludes TXT corpus files. The collector
actually includes every public Android source/asset file regardless of suffix.
Both source-at-build-start.json files list the normalization TXT corpus within
their403 captured inputs. Additional checks in verify_and_record.py confirm the
packaged corpus bytes equal the official file; these checks supplement existing
input capture. No tests, counts, source code, source identities, APKs, raw output
or acceptance result changes. The live methods report is corrected; the original
closure snapshot and gate remain immutable so this correction is auditable.
