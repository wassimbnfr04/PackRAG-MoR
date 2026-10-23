"""Verify cumulative M0-M4 publication source and explicitly declared overlays."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    manifest = json.loads((ROOT / 'docs/publication/M4_SNAPSHOT_MANIFEST.json').read_text(encoding='utf-8'))
    checked = 0
    for name, expected in manifest['baseline_files_sha256'].items():
        actual_name = manifest['original_document_backups'].get(name, name)
        path = ROOT / actual_name
        if not path.is_file() or digest(path) != expected:
            raise RuntimeError('Baseline payload differs: ' + actual_name)
        checked += 1
    for name, expected in manifest['publication_files_sha256'].items():
        path = ROOT / name
        if not path.is_file() or digest(path) != expected:
            raise RuntimeError('Publication payload differs: ' + name)
    for name, expected in manifest['accepted_android_input_sha256'].items():
        if digest(ROOT / name) != expected:
            raise RuntimeError('Accepted Android input differs: ' + name)
    for name, expected in manifest['accepted_current_python_input_sha256'].items():
        if digest(ROOT / name) != expected:
            raise RuntimeError('Accepted product/shared Python input differs: ' + name)
    print(json.dumps(dict(status='PASS_M0_THROUGH_M4_PUBLICATION_BYTES',
        original_checkpoint=manifest['original_checkpoint'],
        preserved_baseline_files=checked,
        publication_files=len(manifest['publication_files_sha256']),
        accepted_android_inputs=len(manifest['accepted_android_input_sha256']),
        accepted_current_python_inputs=len(manifest['accepted_current_python_input_sha256']),
        kotlin_files=manifest['kotlin_files'], java_files=manifest['java_files'],
        compiled_payload_exclusions=manifest['compiled_payload_exclusions'],
        scope='Byte identity and coverage, not a new Android/device acceptance result'), indent=2))


if __name__ == '__main__':
    main()
