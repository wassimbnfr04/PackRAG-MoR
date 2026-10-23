"""Versioned actual system-picker gate; run only in the announced owner foreground window."""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
M4 = ROOT / 'artifacts/v1.3/m4'
ADB = ROOT / 'vendor/platform-tools/adb.exe'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

parser = argparse.ArgumentParser()
parser.add_argument('--run', required=True)
parser.add_argument('--foreground-authorized', action='store_true', required=True)
args = parser.parse_args()
assert args.foreground_authorized
run = M4 / args.run
target = HERE / (args.run + '-execution.json')
assert run.parent == M4 and not run.exists() and not target.exists()
build = M4 / 'build-0073'
assert read(HERE/'viewmodel-complete-0001.json')['status'] == 'PASS_F2_BACKGROUND_VIEWMODEL_ITERATION_NOT_FULL_F2'
assert read(HERE/'build-0069-picker-contracts.json')['status'].startswith('PASS_PACKAGED_TEST_ONLY')
prep = M4/'device-local-asset-picker-preparation-0001'
original = prep/'original-adb/m4-local-asset-picker-preparation.json'
assert read(original)['status'] == 'PASS'
assert sha(original) == read(prep/'collected-results.json')['saved_sha256'][original.name]
sources = read(build/'source-at-build-start.json')['files']
for name, value in sources.items():
    assert sha(ROOT/name) == value, name
files = ['m4-local-asset-import-ui.json', 'm4-local-asset-import-ui-progress.json']
pngs = ['m4-local-asset-import-ui-progress.png', 'm4-local-asset-import-ui-verified.png']
commands = [
    [sys.executable, '-X', 'utf8', str(HERE/'prepare_full_sources.py'), '--build', 'build-0073', '--output', args.run+'-before-source.json', '--verify-only'],
    [sys.executable, '-X', 'utf8', '-m', 'scripts.v13_test_android', '--serial', 'R3CT908DHHR', '--build', str(build), '--run', str(run), '--class-name', 'org.packrag.product.LocalAssetImportUiDeviceTest', '--result-file', files[0], '--timeout', '2400', '--variant', 'debug'],
    [sys.executable, '-X', 'utf8', '-m', 'scripts.v13_collect_phone_results', '--run', str(run), '--files', ','.join(files)],
    [sys.executable, '-X', 'utf8', str(HERE/'prepare_full_sources.py'), '--build', 'build-0073', '--output', args.run+'-after-source.json', '--verify-only'],
    [sys.executable, '-X', 'utf8', str(HERE/'capture_known_guard.py'), '--output', args.run+'-after-known-guard.json'],
]
record = dict(status='RUNNING', started_utc=datetime.now(timezone.utc).isoformat(), runner_sha256=sha(Path(__file__)), build='build-0073', run=args.run, foreground_authorized=True, commands=[])
try:
    for index, command in enumerate(commands):
        print(args.run, 'stage', index, 'START', flush=True)
        with (HERE/(args.run+f'-stage-{index}.stdout.txt')).open('xb') as out, (HERE/(args.run+f'-stage-{index}.stderr.txt')).open('xb') as err:
            result = subprocess.run(command, cwd=ROOT, stdout=out, stderr=err)
        record['commands'].append(dict(argv=command, returncode=result.returncode))
        target.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
        assert result.returncode == 0, 'Hold later milestones; preserve and diagnose this failure'
        if index == 2:
            device = read(run/'original-adb'/files[0])
            saved_png = {}
            for name in pngs:
                command_png = [str(ADB), '-s', 'R3CT908DHHR', 'exec-out', 'run-as', 'org.packrag.product', 'cat', 'files/'+name]
                result_png = subprocess.run(command_png, capture_output=True, timeout=30)
                assert result_png.returncode == 0
                payload = result_png.stdout
                assert payload.startswith(b'\x89PNG\r\n\x1a\n')
                path = run/'original-adb'/name
                path.write_bytes(payload)
                assert sha(path) == device['visual_png'][name]['sha256'] and len(payload) == device['visual_png'][name]['bytes']
                saved_png[name] = sha(path)
            record['png_sha256'] = saved_png
        print(args.run, 'stage', index, 'PASS', flush=True)
    collection = read(run/'collected-results.json')
    device = read(run/'original-adb'/files[0])
    expected = [
        'actual-document-read-denied-before-system-picker-grant',
        'actual-system-picker-cancel-keeps-file-and-completed-result',
        'actual-picked-corrupt-file-rejected-without-replacing-file-or-completion',
        'actual-displayed-byte-progress-and-ui-cancel-wait-for-cleanup',
        'actual-picker-slot-survives-pending-activity-recreation-and-granted-verified-import',
        'asset-page-recreation-back-and-canonical-evidence-navigation-retain-completion',
        'actual-post-import-ui-query-cold-native-and-validated-cited-answer',
        'known-owner-fifty-public-files-unchanged',
    ]
    assert device['status'] == 'PASS' and device['variant'] == 'debug'
    assert [case['id'] for case in device['cases']] == expected and all(case['passed'] is True for case in device['cases'])
    for name in files:
        path = run/'original-adb'/name
        assert sha(path) == collection['saved_sha256'][name]
        value = read(path)
        assert value['status'] == 'PASS' and value['test_id'] == device['test_id'] and value['cases'] == device['cases']
    assert device['guards_unchanged'] is True and device['owner_registry_and_model_sha256'] == read(HERE/'before.json')['owner_public_file_sha256']
    assert 1 <= device['ui_observed_partial_copy_bytes'] <= 5442
    assert '74 °C' in device['answer'] and '[S1]' in device['answer'] and 1 <= device['emitted_tokens'] <= 512
    assert device['initialization_ms'] > 0 and device['completed_result_id_before'] != device['completed_result_id_after']
    assert device['actual_weight_inference'] is True and device['raw_reasoning_persisted'] is False
    recreation = device['pending_picker_recreation']
    assert recreation['requested_lifecycle_state'] in ('CREATED', 'STARTED')
    for field in ['previous_activity_destroyed', 'distinct_activity_created', 'saved_state_bundle_present', 'same_viewmodel', 'picker_still_foreground']:
        assert recreation[field] is True
    assert device['new_query_dispatch_observed'] is True
    audit = device['actual_system_document_open']
    assert audit['last_document_id'] == 'full-template' and audit['calling_uid'] != audit['provider_uid']
    assert audit['document_uri'] == 'content://org.packrag.product.test.asset-documents/document/full-template'
    for when in ['before', 'after']:
        assert read(HERE/(args.run+'-'+when+'-source.json'))['source_sha256'] == read(HERE/'full-source-preparation-0001.json')['source_sha256']
    for name, value in sources.items():
        assert sha(ROOT/name) == value, name
    record.update(status='PASS_F2_SYSTEM_PICKER_PHONE_CONTRACTS_VISUAL_REVIEW_PENDING_NOT_FULL_F2', original_sha256=collection['saved_sha256'], cases=expected,
        scope='Actual Android picker and protected selected-document grant, cancel/corrupt/progress/cancel/recreation/verified import, completed result and canonical navigation, new real cited synthetic native answer. Separate visual review mandatory. Test-only isolated Application/actual ViewModelStore injection; empty launch registry retained. No owner pack authorship, domain/gold/performance/full F2/M4/release acceptance. Mobile data preserved.')
except Exception as failure:
    record.update(status='FAIL', failure_type=type(failure).__name__, failure_message=str(failure))
    if run.exists():
        directory = run/'failure-original-adb'
        directory.mkdir(exist_ok=False)
        captures = {}
        for name in files+pngs:
            result = subprocess.run([str(ADB), '-s', 'R3CT908DHHR', 'exec-out', 'run-as', 'org.packrag.product', 'cat', 'files/'+name], capture_output=True, timeout=30)
            info = dict(returncode=result.returncode, stderr_utf8=result.stderr.decode('utf-8', errors='replace'))
            if result.returncode == 0:
                path = directory/name
                path.write_bytes(result.stdout)
                info['sha256'] = sha(path)
                info['scope'] = 'Unaccepted failure-time capture; may be absent, partial or stale. Interpret against current test_id and progress, never promote to PASS.'
            captures[name] = info
        record['failure_captures'] = captures
    raise
finally:
    record['finished_utc'] = datetime.now(timezone.utc).isoformat()
    target.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
print(record['status'], flush=True)
