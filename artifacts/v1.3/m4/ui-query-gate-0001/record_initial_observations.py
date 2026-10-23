"""Preserve initial build binding and sandbox diagnostic without rewriting results."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
start=json.loads((ROOT/'artifacts/v1.3/m4/build-0032/source-at-build-start.json').read_text())['files']
new=ROOT/'product/android/app/src/androidTest/java/org/packrag/product/QueryControlsPolicyTest.kt'
assert new.relative_to(ROOT).as_posix() not in start
changed={name:digest(ROOT/name) for name,value in start.items() if digest(ROOT/name)!=value};assert not changed
target=HERE/'initial-observations.json';assert not target.exists()
target.write_text(json.dumps(dict(recorded_utc=datetime.now(timezone.utc).isoformat(),
    initial_build='build-0032',build_status='BUILD_SUCCESSFUL_HOST37_NOT_ACCEPTED_FINAL_SOURCE_BINDING',
    problem='One new policy instrumentation source was added after build-start capture; no existing captured source changed. The initial APK is not used for acceptance.',
    added_after_build_start={new.relative_to(ROOT).as_posix():digest(new)},changed_existing_inputs=changed,
    repair='Freeze all E1 sources and rerun fresh debug0033/demo0034 before device acceptance.',
    regression_run='run-0013',regression_status='HELD_FOR_WINDOWS_SANDBOX_TEMP_DIRECTORY_PERMISSION_ERRORS',
    diagnostic='Existing test_valid_pack_and_immutable_query fails writing/cleaning Python TemporaryDirectory with WinError5; no product Python changes.',
    diagnostic_path_probe='First one-test command named absent tests/test_kpack.py and collected zero tests; corrected inventory identified tests/test_kpack_security.py. No acceptance claimed for the probe.',
    repair_regression='Allow original full run to finish. Preserve failure logs/JUnit, rerun fresh versioned outputs with normal host permissions; do not weaken tests or alter global ACLs.',
    source_review_corrections='Before final builds, review corrected normal-result submission override and canonical source hash property name. No accepted device output exists from earlier draft.',
    later_milestones='E2 and beyond remain held'),indent=2)+'\n',encoding='utf-8')
print('Initial evidence limitations recorded; fresh final-source validation required')
