"""Document actual successful recovery, keeping failed orchestration immutable."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
target = HERE / "actual-restoration-document-note.json"
assert not target.exists() and not (HERE / "gate.json").exists()
recovered = json.loads((HERE / "full-background-recovered-execution.json").read_text(encoding="utf-8"))
assert recovered["status"] == "PASS_E3_FULL_DEVELOPMENT_POLICY_RESTORATION_ORIGINALS_NOT_PARITY_OR_CLOSURE"
checks = json.loads((HERE / "final-check-tool-execution.json").read_text(encoding="utf-8"))
assert checks["parity"]["tool_result"]["exit_code"] == checks["check_only"]["tool_result"]["exit_code"] == 0
now = datetime.now(timezone.utc).isoformat()
note = (
    f"\n\nActual E3 restoration/recovery detail, {now}: full0052 development37 and full0053 compiled-policy30 completed successfully, "
    "with all37/30 original JSONs saved before each APK switch. The previously discovered old0014 output-directory collision then actually raised "
    "FileExistsError/WinError183 in v13_test_android.py at mkdir(exist_ok=False), before record construction or any ADB action. "
    "The loaded driver retained its original argv; it was allowed to finish the running full suites without interruption. "
    "full-background-execution.json remains FAIL with its successful firstfour commands and failed fifth command; stage4 stderr remains original. "
    "No historical0014 file was replaced, renamed or promoted. recover_restoration.py rechecked their five public hashes and every574 current Android input, "
    "required both full-suite PASS manifests/all67 originals, then executed fresh0052 consent0015 and its original collector. "
    "The new restoration passes one method/four controls in4.014 JUnit seconds. full-background-recovered-execution.json binds the prior failure and the actual new commands; "
    "it does not relabel the failed driver or imply a full-suite rerun. Latest verify_full_parity_restoration_final.py and verify_and_record_final.py --check-only both actually pass, "
    "with tool outputs/durations recorded in final-check-tool-execution.json. The document-update helper repeated check-only before recording acceptance. "
    "The policy progress observer also refused a single current PID immediately after the suite ended; its underlying PID stdout/return were not retained, "
    "so absence versus multiple PIDs is not inferred. No progress JSON was created by that refusal. This observation is separate from the terminal30-method PASS and originals. "
    "E3 closure/checkpoint follow; no phone test is currently running. This closes diagnostics/execution/lifecycle/UI acceptance only, not M4F, final content, factual gold accuracy or release performance.\n"
)
for name in ["docs/v1.3/FULL_DOCUMENTATION_WORKING.md", "docs/v1.3/M4E3_EVIDENCE_INDEX.md", "DECISIONS.md"]:
    with (ROOT / name).open("a", encoding="utf-8") as stream:
        stream.write(note)
target.write_text(json.dumps(dict(status="ACTUAL_E3_RECOVERY_AND_OBSERVATIONAL_ERRORS_DOCUMENTED_BEFORE_CLOSURE", recorded_utc=now,
    documents=["docs/v1.3/FULL_DOCUMENTATION_WORKING.md", "docs/v1.3/M4E3_EVIDENCE_INDEX.md", "DECISIONS.md"], note=note), indent=2) + "\n", encoding="utf-8")
print("Actual restoration collision, fresh recovery and progress-observer limits documented")
