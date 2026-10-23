"""Verify accepted E3 before first F runtime edit and save public before-sources."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
target = HERE / "preimplementation.json"
assert not target.exists()

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

gate_path = ROOT / "artifacts/v1.3/m4/diagnostics-gate-0001/gate.json"
gate = read(gate_path)
assert gate["status"] == "M4E3_OWNED_DIAGNOSTICS_EXECUTION_LIFECYCLE_AND_UI_VERIFIED_NOT_COMPLETE_M4_OR_PRODUCT"
head = subprocess.run(["git", "--no-optional-locks", "-c", "safe.directory=" + ROOT.as_posix(), "rev-parse", "HEAD"], cwd=ROOT,
    capture_output=True, text=True, check=True).stdout.strip()
assert head == "ac98b4fa6b9fd89b9f0f53023cb1f6115408567f"
for name, expected in {**gate["source_sha256"], **gate["android_source_sha256"], **gate["output_sha256"]}.items():
    assert sha(ROOT / name) == expected, name
names = ["ProductSession.kt", "PackRagViewModel.kt", "MainActivity.kt"]
before = {}
for name in names:
    relative = "product/android/app/src/main/java/org/packrag/product/" + name
    path = HERE / "before-sources" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    assert not path.exists()
    path.write_bytes((ROOT / relative).read_bytes())
    before[relative] = sha(path)
record = dict(status="PASS_E3_CHECKPOINT_AND_PUBLIC_INPUTS_BEFORE_F1_IMPLEMENTATION", recorded_utc=datetime.now(timezone.utc).isoformat(),
    head=head, prior_gate_sha256=sha(gate_path), android_source_sha256=gate["android_source_sha256"], runtime_source_sha256=gate["source_sha256"],
    prior_public_outputs=len(gate["output_sha256"]), before_source_snapshots=before,
    fixed_acceptance_document_sha256=sha(ROOT / "docs/v1.3/M4F1_ASSET_CONTRACT.md"), scope="Public source/evidence only; no private custody, model reads or phone mutation. F1 code and acceptance remain pending.")
target.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
note = f"M4F1 IMPLEMENTING at {record['recorded_utc']} after verified E3/ac98b4f. Preimplementation guard verifies574 Android/188 runtime inputs and every prior E3 public output; before-sources and independent acceptance are saved in asset-readiness-gate-0001/M4F1_ASSET_CONTRACT.md. First integrate read-only pinned four-file readiness, actionable query errors and the real asset-check screen; relevant host/contracts/actual background walking and UI/visual must pass before F2 URI staging/import. F3 normative presentation/F4 final M4/software builder/evaluation/release/physical metrics/documentation/three archives remain. Owner supplies final knowledge content. No phone test is running; mobile data stays on."
for name in ["STATUS.md", "PLAN.md"]:
    path = ROOT / name
    first, rest = path.read_text(encoding="utf-8-sig").split("\n", 1)
    path.write_text(first + "\n\n" + note + "\n\n" + rest, encoding="utf-8")
for name in ["DECISIONS.md", "docs/v1.3/FULL_DOCUMENTATION_WORKING.md", "docs/v1.3/M4_IMPLEMENTATION_LOG.md"]:
    with (ROOT / name).open("a", encoding="utf-8") as stream:
        stream.write("\n\n" + note + "\nFixed four existing paths/pins; no alternate model/profile/trust store or network downloader. Pure readiness precedes URI import; URI failures belong to F2. Existing constructors retain independent hash checks. No architecture change or final-pack authorship is introduced.\n")
print(record["status"])
