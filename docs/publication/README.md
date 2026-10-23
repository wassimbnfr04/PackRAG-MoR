# Full project through M4: publication record

This snapshot contains the cumulative repository at original checkpoint
8f0ccaa5cfac125c2ec2adf291cef3d1d7d4c3b0, not just its last commit diff.
No later source,21October guide or18October free-answer experiment is included.
A fresh Git history is used so unrelated working-tree files and prior objects
cannot be accidentally pushed. The source checkpoint identity remains recorded.

Publication changes: a current top-level README/STATUS, strengthened ignore
rules, setup/model notes and this provenance record. Original checkpoint
README/STATUS/gitignore are preserved under original-checkpoint-docs.
Three old compiled APK/JAR payloads are omitted; their original hashes remain in
SOURCE_CLEANLINESS_REVIEW.json and the original local evidence is untouched.
Retained build-* directories contain historical text/XML logs and manifests,
not generated SDK/build installations.

Verification:
- All640 accepted Android build inputs match, including176 Kotlin and3 Java.
- All accepted product Python/runtime/test/shared-format source present in the
  checkpoint matches its recorded hashes. ACCEPTED_SOURCE_COMPARISON lists
 12uncommitted legacy Week-1 utilities and1different legacy finalizer that were
  outside the exact public checkpoint; they are not silently mixed into it.
- Fresh exported-tree regression:1054 passed in61.41s, no skips/failures/errors;
  original JUnit is publication-regression-0001.xml. Original M4 physical results
  remain historical; no new phone run is implied by this publication.
- Baseline file hashes and controlled documentation overlays are independently
  checked by verify_m4_snapshot.py.
- Snapshot filenames/sizes and listed credential patterns were reviewed. No
  actual publisher-private custody, weights, SDKs/caches or copied old .git
  history are included. A documented public test seed is intentionally retained.
  This bounded check does not claim universal secret detection/license clearance.

Run python scripts/verify_m4_snapshot.py from this repository to verify the
recorded original payload, source coverage and publication-document identities.
Model/toolchain assets remain separate; see docs/GETTING_STARTED_M4.md.
First-party licensing has not been selected or invented for this publication.
