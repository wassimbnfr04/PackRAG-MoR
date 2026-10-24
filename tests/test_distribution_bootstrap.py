import hashlib
import io
import json
from pathlib import Path
import zipfile

import pytest
from scripts import bootstrap_packrag as boot


def entry(data, path='assets/model'):
    return {'path': path, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'url': 'https://example.invalid/model'}


@pytest.mark.parametrize('name', ['../outside', '/absolute', 'C:/outside', 'nested/../../outside'])
def test_dependency_target_cannot_escape_root(tmp_path, name):
    with pytest.raises(ValueError):
        boot.target(tmp_path, name)


def test_local_dependency_copy_verifies_before_acceptance_and_keeps_source(tmp_path):
    source = tmp_path / 'source'; source.mkdir()
    (source / 'asset').write_bytes(b'fixed bytes')
    root = tmp_path / 'clone'; root.mkdir()
    assert boot.acquire(root, entry(b'fixed bytes', 'asset'), source_root=source) == 'INSTALLED_HASH_VERIFIED'
    assert (root / 'asset').read_bytes() == (source / 'asset').read_bytes() == b'fixed bytes'
    assert not list(root.glob('*.part-*'))


def test_existing_wrong_model_is_preserved_without_download(tmp_path, monkeypatch):
    (tmp_path / 'model').write_bytes(b'owner bytes')
    monkeypatch.setattr(boot.urllib.request, 'urlopen', lambda *a, **k: pytest.fail('must not download'))
    with pytest.raises(ValueError):
        boot.acquire(tmp_path, entry(b'correct', 'model'), download=True)
    assert (tmp_path / 'model').read_bytes() == b'owner bytes'


def test_download_mismatch_never_installs_partial(tmp_path, monkeypatch):
    monkeypatch.setattr(boot.urllib.request, 'urlopen', lambda *a, **k: io.BytesIO(b'wrong'))
    with pytest.raises(ValueError):
        boot.acquire(tmp_path, entry(b'right', 'model'), download=True)
    assert not (tmp_path / 'model').exists()
    assert not list(tmp_path.glob('*.part-*'))


def test_oversize_download_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(boot.urllib.request, 'urlopen', lambda *a, **k: io.BytesIO(b'excess bytes'))
    with pytest.raises(ValueError, match='exceeds'):
        boot.acquire(tmp_path, entry(b'few', 'model'), download=True)
    assert not (tmp_path / 'model').exists()


def test_verify_only_does_not_copy_or_contact_network(tmp_path, monkeypatch):
    source = tmp_path / 'source'; source.mkdir(); (source / 'model').write_bytes(b'ok')
    root = tmp_path / 'clone'; root.mkdir()
    monkeypatch.setattr(boot.urllib.request, 'urlopen', lambda *a, **k: pytest.fail('must not download'))
    assert boot.acquire(root, entry(b'ok', 'model'), source_root=source, verify_only=True) == 'VERIFIED_LOCAL_SOURCE_NOT_INSTALLED'
    assert not (root / 'model').exists()


def test_no_implicit_large_download(tmp_path, monkeypatch):
    monkeypatch.setattr(boot.urllib.request, 'urlopen', lambda *a, **k: pytest.fail('must not download'))
    with pytest.raises(FileNotFoundError):
        boot.acquire(tmp_path, entry(b'ok', 'model'))


@pytest.mark.parametrize('member', ['../escaped', 'top/../../escaped', '/absolute'])
def test_archive_traversal_checked_before_stripping_prefix(tmp_path, member):
    archive = tmp_path / 'package.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr(member, b'bad')
    with pytest.raises(ValueError):
        boot.extract_archive(archive, tmp_path / 'stage', True)
    assert not (tmp_path / 'escaped').exists()


def test_archive_root_is_stripped_for_real_sdk_layout(tmp_path):
    archive = tmp_path / 'package.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('tool/bin/launcher', b'executable fixture')
    boot.extract_archive(archive, tmp_path / 'stage', True)
    assert (tmp_path / 'stage/bin/launcher').read_bytes() == b'executable fixture'


def test_asset_manifest_matches_original_runtime_pins_and_not_training_weights():
    root = Path(__file__).resolve().parents[1]
    manifest = boot.load(root / 'product/config/asset-downloads.json')['assets']
    lock = boot.load(root / 'product/config/toolchain.lock.json')
    indexed = {e['path']: e for e in manifest}
    assert indexed[lock['generator']['artifact']]['sha256'] == lock['generator']['sha256']
    for name, expected in lock['embedder']['asset_sha256'].items():
        assert indexed['models/v1.3/granite/' + name]['sha256'] == expected
    assert not any(e['path'].endswith('.safetensors') for e in manifest)
    assert all('/resolve/' in e['url'] and '/resolve/main/' not in e['url'] for e in manifest)


def test_checked_in_wrapper_verifies_the_exact_distribution():
    root = Path(__file__).resolve().parents[1]
    properties = (root / 'product/android/gradle/wrapper/gradle-wrapper.properties').read_text()
    assert 'gradle-9.6.0-bin.zip' in properties
    assert 'distributionSha256Sum=bbaeb2fef8710818cf0e261201dab964c572f92b942812df0c3620d62a529a01' in properties
    wrapper = root / 'product/android/gradle/wrapper/gradle-wrapper.jar'
    assert boot.digest(wrapper) == '497c8c2a7e5031f6aa847f88104aa80a93532ec32ee17bdb8d1d2f67a194a9c7'


def test_portable_launcher_does_not_read_historical_machine_inventory():
    root = Path(__file__).resolve().parents[1]
    text = (root / 'scripts/build_android_portable.ps1').read_text()
    assert 'android_tool_paths.json' not in text
    assert '.packrag.local.json' in text and 'gradlew.bat' in text
