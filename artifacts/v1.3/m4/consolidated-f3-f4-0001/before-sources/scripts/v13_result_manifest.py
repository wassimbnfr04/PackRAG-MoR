"""Record an existing test run and recheck historical identities without rewriting them."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def public_path(root,path):
    root=root.resolve(); blocked={'.private','build','.gradle','.kotlin','.cxx','__pycache__'}
    if not path.is_relative_to(root) or blocked.intersection(path.relative_to(root).parts): return False
    resolved=path.resolve()
    return resolved.is_relative_to(root) and not blocked.intersection(resolved.relative_to(root).parts)

def public_source_files(root):
    """Never read private custody or generated build/cache trees into public reports."""
    root=root.resolve()
    files=[]
    for top in ('product','scripts'):
        for path in (root/top).rglob('*'):
            if not public_path(root,path) or path.suffix not in ('.py','.json','.sql') or not path.is_file(): continue
            files.append(path)
    return files


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--command", required=True)
    args = parser.parse_args()
    output = args.run / "result-manifest.json"
    if output.exists():
        raise RuntimeError("Result manifests are immutable; choose a new run directory")
    suites = [ET.parse(path).getroot().find("testsuite") for path in args.run.glob("*-junit.xml")]
    if not suites:
        raise RuntimeError("No JUnit evidence in requested run")
    totals = {key: sum(int(suite.attrib.get(key, 0)) for suite in suites)
              for key in ("tests", "failures", "errors", "skipped")}
    historical = json.loads((ROOT / "artifacts/v1.3/m0/historical-evidence-guard.json").read_text(encoding="utf-8"))["files"]
    changed = [name for name, expected in historical.items() if digest(ROOT / name) != expected]
    if changed:
        raise RuntimeError("Historical evidence changed: " + repr(changed))
    sources = public_source_files(ROOT)
    sources += [ROOT / name for name in ("PLAN.md", "STATUS.md", "DECISIONS.md")]
    command = ["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"]
    commit = subprocess.check_output(command, cwd=ROOT, text=True).strip()
    record = dict(recorded_at=datetime.now(timezone.utc).isoformat(), command=args.command,
                  git_commit=commit, source_identity="DIRTY_WORKTREE_CAPTURED_AT_MANIFEST_RECORDING",
                  source_capture_note="These hashes were captured when this manifest was written; they are not a claim that untested files were tested or that the worktree was unchanged since the test began.",
                  totals=totals, historical_checked=len(historical), historical_unchanged=True,
                  status="PASS" if totals["failures"] == totals["errors"] == 0 else "FAIL",
                  source_sha256={path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(sources)},
                  output_sha256={path.name: digest(path) for path in args.run.iterdir() if path.is_file()})
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: record[key] for key in ("status", "totals", "historical_checked")}, indent=2))


if __name__ == "__main__":
    main()
