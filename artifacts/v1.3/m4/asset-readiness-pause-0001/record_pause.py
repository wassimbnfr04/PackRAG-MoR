"""Record an owner-requested pause; run no builds, tests or device commands."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
HEAD = 'ac98b4fa6b9fd89b9f0f53023cb1f6115408567f'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def git(*args):
    return subprocess.check_output(['git', '--no-optional-locks', '-c',
        'safe.directory=' + ROOT.as_posix(), '-c', 'core.autocrlf=false',
        *args], cwd=ROOT, text=True).strip()

target = HERE / 'pause.json'
assert not target.exists(), 'Pause records are immutable'
assert git('rev-parse', 'HEAD') == HEAD
assert not git('diff', '--cached', '--name-only'), 'Unexpected staged changes'
build = ROOT / 'artifacts/v1.3/m4/build-0054'
iteration = ROOT / 'artifacts/v1.3/m4/asset-readiness-gate-0001/first-host-iteration.json'
first = read(iteration)
assert read(build / 'build-result.json')['exit_code'] == 0
assert first['host_totals'] == dict(tests=62, failures=0, errors=0, skipped=0)
sources = read(build / 'source-at-build-start.json')['files']
assert len(sources) == 577
# Read only previously enumerated public build inputs, never scan private custody.
for name, expected in sources.items():
    assert not any(part in {'.private', 'temp'} for part in Path(name).parts)
    assert sha(ROOT / name) == expected, name
for name, expected in first['source_snapshots'].items():
    assert sources[name] == expected
    assert sha(iteration.parent / 'first-host-sources' / name) == expected
gate = ROOT / 'artifacts/v1.3/m4/diagnostics-gate-0001/gate.json'
now = datetime.now(timezone.utc).isoformat()
statement = (
    f'OWNER PAUSED at {now}. All tracked current builds/tests have completed; '
    'none were killed. No new phone test will start until the owner explicitly resumes '
    'with the phone available. The phone can be disconnected. '
    f'M4E3 is verified and committed at {HEAD}. '
    'Current work is M4F1 local asset readiness: build-0054 completed successfully, '
    '62 host methods passed with zero failures/errors/skips, and all 577 public Android '
    'build inputs still match the tested snapshot. Six F1 source changes and their '
    'tested bytes are retained in asset-readiness-gate-0001/first-host-sources. '
    'Build-0054 has not been installed; F1 phone/native/UI validation has not started. '
    'F1 is unfinished and uncommitted, not an accepted milestone. '
    'Next on resume: verify this pause snapshot, review failed-query asset-status '
    'presentation, then add/run F1 physical readiness/native/UI and adjacent regressions '
    'before F2. F2 import, F3 presentation, F4 full M4 audit, builder/evaluation software, '
    'final Android release/physical measurements and documentation/three archives remain. '
    'Final knowledge content remains owner supplied; permitted test packs may be used. '
    'Mobile data remains on. Historical evidence and the earlier default-registry '
    'byte-change exception remain unchanged. Functional timings are not performance '
    'benchmarks, and host success does not establish phone acceptance.'
)
docs = ['STATUS.md', 'PLAN.md', 'DECISIONS.md',
        'docs/v1.3/FULL_DOCUMENTATION_WORKING.md',
        'docs/v1.3/M4_IMPLEMENTATION_LOG.md']
doc_hashes = {}
for name in docs:
    path = ROOT / name
    content = path.read_text(encoding='utf-8-sig')
    if name in {'STATUS.md', 'PLAN.md'}:
        heading, separator, rest = content.partition('\n')
        content = heading + '\n\n' + statement + '\n\n' + rest
    else:
        content = content.rstrip() + '\n\n## Owner-requested pause ' + now + '\n\n' + statement + '\n\n' + (
            'No build/test/device command was launched for this pause. A read-only '
            'process inventory via Get-CimInstance was denied by the sandbox; it '
            'does not prove process absence. Completion is established by the '
            'tracked terminal sessions and saved terminal result manifests. No '
            'process was terminated. The pending failed-query asset-status display '
            'review is a code-review concern, not an observed failing test.\n')
    path.write_text(content, encoding='utf-8')
    snapshot = HERE / 'documents-at-pause' / name
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    assert not snapshot.exists()
    snapshot.write_bytes(path.read_bytes())
    doc_hashes[name] = sha(snapshot)
record = dict(
    status='OWNER_PAUSED_M4F1_HOST_ITERATION_NOT_DEVICE_OR_MILESTONE_ACCEPTANCE',
    recorded_utc=now, accepted_checkpoint=HEAD, accepted_e3_gate_sha256=sha(gate),
    first_host_iteration_sha256=sha(iteration), build_result_sha256=sha(build / 'build-result.json'),
    host_totals=first['host_totals'], android_source_sha256=sources,
    tested_f1_source_sha256=first['source_snapshots'], documents_at_pause_sha256=doc_hashes,
    current_tracked_tests='ALL_TERMINAL_COMPLETED', tests_killed=False,
    new_tests_started_for_pause=False, f1_phone_validation_started=False,
    build_0054_installed=False, f1_accepted=False, resume_requires_explicit_owner_instruction=True,
    process_inventory='CIM_DENIED_NO_ABSENCE_INFERENCE; tracked terminal manifests establish completion',
    statement=statement)
target.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print('OWNER_PAUSE_SAVED: E3 committed; F1 62 host tests passed; device validation pending; no tests started or killed.')
