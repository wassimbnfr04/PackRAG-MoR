# ADR-003: Session chat presentation for M4

Status: accepted implementation direction, 2026-10-12; validation pending.

The owner requested a ChatGPT-style mobile interface and meaningful repair-guide evaluation. The previous home screen exposed a development form, with only the latest completed answer. Its 74°C smoke check established pipeline operation, not general repair competence.

Use a neutral chat layout with a fixed composer, completed question/answer turns, explicit source actions, pack management, local assets, query controls and diagnostics. Keep PackRAG branding. Retain up to12 completed turns in the ViewModel only; no disk chat store, raw reasoning, native handles or hidden question rewriting. Each question still traverses the existing v1.3 verified-pack/retrieval/admission/selection/LFM/output-validation path independently. An earlier turn's source navigation uses its own immutable result ID and captured evidence, never the latest answer's S1 by accident. New chat clears presentation results without changing packs or local assets. Process recreation retains primitive navigation/form values only, and unavailable prior results fail closed.

The UI change does not alter model weights, evidence budgets, retrieval thresholds, generation settings, trust policy or calibrated-pack requirements. Repair test documents and gold are versioned and frozen before inference; derived test material and development trust remain explicitly distinguished from final owner packs, human-reviewed calibration and release approval.

Accept only after relevant host ownership/navigation contracts, adjacent ViewModel/security/asset/cancellation checks, actual emulator layout/keyboard/large-font/picker flows with original image review, broad real-generator repair checks and required desktop/Android integration pass. Use unchanged dependency identities for warranted historical regression reuse; do not rerun whole suites for unrelated presentation edits. Physical hardware acceptance remains physical.
