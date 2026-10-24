"""Restore the pinned public dependencies omitted from the Git source tree.

Python standard library only. Downloads occur only with --download. Existing
wrong files/directories are never silently overwritten. Private keys are not
inputs to bootstrap or to running an already-signed development pack.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import urllib.request
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def target(root, relative):
    name = relative.replace('\\', '/')
    parts = PurePosixPath(name).parts
    if not parts or name.startswith('/') or ':' in name or '..' in parts:
        raise ValueError('Unsafe dependency path: ' + relative)
    root = root.resolve()
    result = root.joinpath(*parts)
    current = root
    for part in parts:
        current = current / part
        if current.exists():
            info = current.lstat()
            if current.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Dependency path crosses a link: ' + relative)
    if not result.resolve().is_relative_to(root):
        raise ValueError('Dependency path escapes root')
    return result


def verify(path, entry):
    if not path.is_file() or path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
        raise ValueError('Missing/wrong dependency bytes: ' + str(path))


def acquire(root, entry, *, source_root=None, download=False, verify_only=False):
    destination = target(root, entry['path'])
    if destination.exists():
        verify(destination, entry)
        return 'VERIFIED_INSTALLED'
    source = target(source_root, entry['path']) if source_root else None
    if source and source.exists():
        verify(source, entry)
        if verify_only:
            return 'VERIFIED_LOCAL_SOURCE_NOT_INSTALLED'
    elif not download or verify_only:
        raise FileNotFoundError(str(destination) + ': supply --from-root or explicitly use --download')
    else:
        source = None
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + '.part-' + uuid.uuid4().hex)
    try:
        request = source.open('rb') if source else urllib.request.urlopen(entry['url'], timeout=300)
        with request as incoming, partial.open('xb') as outgoing:
            size = 0
            while True:
                block = incoming.read(1024 * 1024)
                if not block:
                    break
                size += len(block)
                if size > entry['bytes']:
                    raise ValueError('Dependency response exceeds pinned size')
                outgoing.write(block)
        verify(partial, entry)
        # Same-filesystem hard link creates the final name atomically and fails
        # if another writer has created it; only our staged file is then removed.
        os.link(partial, destination)
        return 'INSTALLED_HASH_VERIFIED'
    finally:
        partial.unlink(missing_ok=True)


def extract_archive(archive, staging, strip_root):
    staging.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        names = [x.filename.replace('\\', '/') for x in z.infolist() if x.filename]
        for name in names:
            target(staging, name)  # Check BEFORE stripping any archive prefix.
        roots = {PurePosixPath(n).parts[0] for n in names}
        if strip_root and len(roots) != 1:
            raise ValueError('Expected one archive root')
        for item in z.infolist():
            mode = (item.external_attr >> 16) & 0xffff
            if stat.S_ISLNK(mode):
                raise ValueError('Archive symlinks are not accepted')
            name = item.filename.replace('\\', '/')
            if strip_root:
                name = name.partition('/')[2]
            if not name:
                continue
            destination = target(staging, name)
            if item.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with z.open(item) as incoming, destination.open('xb') as outgoing:
                    shutil.copyfileobj(incoming, outgoing, 1024 * 1024)


def git(root, *args):
    command = ['git', '-c', 'safe.directory=' + root.resolve().as_posix(), '-C', str(root), *args]
    return subprocess.check_output(command, text=True, encoding='utf-8').strip()


def native(root, install=False):
    expected = load(root / 'product/config/toolchain.lock.json')['generator']['llama_cpp_commit']
    path = root / 'vendor/llama.cpp'
    if install and not (path / 'CMakeLists.txt').exists():
        git(root, 'submodule', 'update', '--init', '--depth', '1', '--', 'vendor/llama.cpp')
    if not (path / 'CMakeLists.txt').is_file():
        raise FileNotFoundError('Run: git submodule update --init --depth 1 -- vendor/llama.cpp')
    if git(path, 'rev-parse', 'HEAD') != expected or git(path, 'status', '--porcelain'):
        raise ValueError('llama.cpp must be clean at ' + expected)
    return {'status': 'PINNED_NATIVE_SOURCE_VERIFIED', 'commit': expected}


def configure(root, sdk, java_home=None):
    sdk = Path(sdk).resolve()
    if not sdk.is_dir():
        raise FileNotFoundError('Android SDK directory not found: ' + str(sdk))
    if not java_home:
        java_home = os.environ.get('JAVA_HOME')
    if not java_home:
        candidates = sorted((root / 'vendor/java').glob('jdk-17*'))
        java_home = candidates[0] if candidates else None
    if not java_home:
        raise FileNotFoundError('Set JAVA_HOME to JDK17 or install the pinned Windows tools')
    java_home = Path(java_home).resolve()
    executable = java_home / 'bin' / ('java.exe' if os.name == 'nt' else 'java')
    version = subprocess.run([str(executable), '-version'], capture_output=True, text=True, check=True)
    if 'version "17.' not in version.stderr + version.stdout:
        raise ValueError('The M4 toolchain requires JDK17')
    record = {'schema_version': 1, 'sdk': str(sdk), 'jdk': str(java_home),
              'python': sys.executable, 'gradle_user_home': str(root / '.cache/gradle')}
    (root / '.packrag.local.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    properties = root / 'product/android/local.properties'
    properties.write_text('sdk.dir=' + sdk.as_posix() + '\n', encoding='utf-8')
    return record


def tools(root, *, download=False, archive_root=None, adb_only=False):
    if os.name != 'nt':
        raise RuntimeError('This pinned archive installer targets Windows x64; use the documented platform SDK on other hosts')
    entries = load(root / 'product/config/windows-toolchain-downloads.json')['archives']
    selected = [e for e in entries if e['kind'] != 'gradle-archive-for-offline-use' and (not adb_only or e['package'] == 'platform-tools')]
    for entry in selected:
        installed = target(root, entry['install_root'])
        marker = installed / '.packrag-bootstrap.json'
        if marker.is_file() and load(marker).get('archive_sha256') == entry['sha256']:
            print(entry['package'], 'ALREADY_INSTALLED', flush=True)
            continue
        if installed.exists():
            raise FileExistsError('Refuse to replace existing tools; configure their paths instead: ' + str(installed))
        archive_entry = {**entry, 'path': 'vendor/downloads/' + entry['archive']}
        if archive_root:
            existing = Path(archive_root) / entry['archive']
            verify(existing, entry)
            archive = existing
        else:
            acquire(root, archive_entry, download=download)
            archive = target(root, archive_entry['path'])
        installed.parent.mkdir(parents=True, exist_ok=True)
        staging = installed.with_name(installed.name + '.stage-' + uuid.uuid4().hex)
        # A failed stage is retained for diagnosis; it is never accepted as final.
        extract_archive(archive, staging, entry['strip_archive_root'])
        if entry.get('metadata'):
            metadata = target(root, entry['metadata'])
            if digest(metadata) != entry['metadata_sha256']:
                raise ValueError('SDK metadata identity mismatch')
            shutil.copyfile(metadata, staging / 'package.xml')
        (staging / '.packrag-bootstrap.json').write_text(json.dumps({'archive_sha256': entry['sha256']}) + '\n', encoding='utf-8')
        staging.rename(installed)
        print(entry['package'], 'INSTALLED_VERIFIED_ARCHIVE', flush=True)
    if not adb_only:
        configure(root, root / 'vendor/android-sdk')
        print('Review/accept Android SDK licenses with vendor/android-sdk/cmdline-tools/latest/bin/sdkmanager.bat --sdk_root=vendor/android-sdk --licenses')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    assets = sub.add_parser('assets', help='Verify/copy/download all exact runtime model assets')
    assets.add_argument('--download', action='store_true')
    assets.add_argument('--from-root', type=Path)
    assets.add_argument('--verify-only', action='store_true')
    assets.add_argument('--build-only', action='store_true', help='Only tokenizer/config/template needed by host build tests; omit GGUF and ONNX weights')
    source = sub.add_parser('native', help='Verify or initialize the pinned source submodule')
    source.add_argument('--install', action='store_true')
    android = sub.add_parser('configure', help='Use an already-installed local SDK/JDK')
    android.add_argument('--sdk', required=True)
    android.add_argument('--java-home')
    windows = sub.add_parser('tools', help='Install exact Windows SDK/JDK archives; Gradle uses its wrapper')
    windows.add_argument('--download', action='store_true')
    windows.add_argument('--archive-root', type=Path)
    windows.add_argument('--adb-only', action='store_true')
    args = parser.parse_args()
    if args.action == 'assets':
        for entry in load(ROOT / 'product/config/asset-downloads.json')['assets']:
            if args.build_only and entry['path'].endswith(('.gguf', '.onnx')):
                continue
            result = acquire(ROOT, entry, source_root=args.from_root, download=args.download, verify_only=args.verify_only)
            print(entry['path'], result, flush=True)
    elif args.action == 'native':
        print(json.dumps(native(ROOT, args.install), indent=2))
    elif args.action == 'configure':
        print(json.dumps(configure(ROOT, args.sdk, args.java_home), indent=2))
    elif args.action == 'tools':
        tools(ROOT, download=args.download, archive_root=args.archive_root, adb_only=args.adb_only)


if __name__ == '__main__':
    main()
