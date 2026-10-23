# M4F1 — pinned local-asset readiness and integrated query gate

Written before F runtime edits, after verified E3 checkpoint ac98b4fa6b9fd89b9f0f53023cb1f6115408567f. This is the first integrated F increment, not completion of F or the product. Final knowledge content remains owner supplied. Existing signed test packs are sufficient for this increment.

The four production slots are fixed beneath the existing private models directory. Their exact public identities are unchanged:

| Slot | Relative path | Expected bytes | Expected SHA256 |
| --- | --- | ---: | --- |
| Generator | LFM2.5-2.6B-QAD-Q4_0.gguf | 1593894944 | a247afd6414918eac8e520a9e6137dc271235461ecbe1180462221d5b8d40b03 |
| Template | chat_template.jinja | 5443 | ea663864491de7ade391839479860ca95541f892f72665c73251fbd4643b1bef |
| Tokenizer | granite/tokenizer.json | 25301672 | 4f2842d568e2724370aec203652a42ac783c7937f8347a1a2cc7506d71f1582f |
| Encoder | granite/onnx/model.onnx | 390004608 | 68e592b160673d30250824c1116bc6ab33f70efb22b97c9e1d7ce1e69c1c9d70 |

Generator size/hash and all hashes come from the shipped public lock. Encoder/tokenizer sizes come from the existing public acquisition manifest. The template size is independently bound to its shipped hash by the read-only E3 template-bound-preparation.json. Configured identities describe expected files; observed verification describes the completed check only. Never label an unchecked filename as verified, or silently trust a stale readiness label when loading.

Implement a read-only bounded verifier and the actual session readiness gate first. It performs no download, import, deletion or model initialization. It rejects unsafe paths before reading bytes, checks regular-file size and exact streaming SHA256, and distinguishes UNCHECKED, MISSING, WRONG_SIZE, CORRUPT, UNREADABLE, UNSAFE_PATH and VERIFIED. Results own immutable values. Existing model constructors retain independent hash checks. No active pack returns NO_ACTIVE_PACK before asset checking/loading. An active query with missing/corrupt assets fails safely before native/encoder initialization, with an actionable local-asset code. A warm session keeps its existing generation behavior. Checking readiness is serialized with session actions and preserves a previously completed answer/source/trace identity; asset replacement is not part of this increment.

Add the smallest real product screen: local-asset configuration, last completed verification status, an explicit check action and missing/corrupt guidance. Keep primitive navigation state, busy/back behavior, safe system-bar spacing and buffered output. Do not move the existing query/source workflow into a disconnected prototype.

## Fixed acceptance groups

1. **Pure/format contracts:** exactly four fixed slots/paths/public pins; lowercase64-character hashes/positive bounded sizes; missing and empty/truncated/oversized files; same-size wrong bytes; correct bytes; wrong-slot bytes; directory and unsafe-path rejection; unreadable/error behavior; cancellation while streaming; no writes or arbitrary destination selection. Small independent fixtures prove verifier behavior only, not actual model readiness.
2. **Session adjacency:** no-pack/missing-assets skips all initialization; active signed pack/missing or corrupt assets produces a deterministic safe error before constructors; all four real pinned assets verify before actual generation; configured lock and fixed-slot identities agree; existing constructor checks/IO bridge/cancellation/registry monitor remain intact. Test-only ContextWrapper filesDir can isolate negative cases without altering owner model files or exposing a production alternate-root setting.
3. **Actual walking path:** verified signed pack → retrieval/admission/selection → actual pinned LFM2.5 → reasoning removal → accepted74°C/[S1]/owned canonical source; unrelated question abstains with zero generation. Collect new original device results under a new F output location and verify source/APK identities. Owner models/partials/default registries and mobile-data state remain protected.
4. **Product read-only check:** explicit status check performs real IO and no model initialization; completed answer/submission/trace/result ID are preserved; new query/mutation invalidation and all retained navigation rules still apply. Actual UI acceptance and independent image review are required for the screen, after its background contracts pass.
5. **Regressions and custody:** all existing relevant host unit/interface tests plus new cases pass; unchanged188 Python-runtime identities permit explicitly retained1034-test evidence at this increment, with a fresh complete Python run required at final F4. Fresh actual affected runtime/diagnostic/readiness smoke and required adjacent cases pass before expansion. All previous E3 public outputs, source snapshots and historical identities remain immutable. Failures are saved and repaired before F2 or later increments.

F2 supplies the local document-picker/URI transport, bounded private staging, atomic verified commit, actual copy cancellation, restart/fault tests and real pinned-artifact import. Therefore source-URI failure cases from the broader F preparation belong to that first URI-consuming increment; they are not represented as tested by this read-only verifier. F3 supplies remaining normative pack/chip/progress presentation. F4 requires fresh complete matched host/Python/desktop/device/security/retrieval/generation/UI/parity/restoration/closure gates. No F1 iteration is described as completing those later requirements.
