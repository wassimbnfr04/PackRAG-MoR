from scripts.v13_result_manifest import public_source_files, public_path

def test_android_binary_source_boundary_and_external_paths(tmp_path):
    assert public_path(tmp_path,tmp_path/'product/android/app/src/main/source.kt')
    assert public_path(tmp_path,tmp_path/'product/android/app/src/main/assets/release-trust.json')
    assert not public_path(tmp_path,tmp_path/'product/android/.private/publisher.seed')
    assert not public_path(tmp_path,tmp_path/'product/android/app/build/generated/config.java')
    assert not public_path(tmp_path,tmp_path.parent/'outside-secret.json')

def test_private_json_and_generated_files_never_enter_public_manifest_hash_inputs(tmp_path):
    public=['product/config/release-trust.json','product/packrag/example.py','product/tests/fixture.json','scripts/runner.py']
    excluded=['product/.private/publisher.json','product/.private/nested/config.py','product/android/build/generated/config.json','product/android/app/build/intermediates/secret.json','product/android/.gradle/config.json','product/android/.cxx/config.json','product/android/.kotlin/config.json','product/packrag/__pycache__/example.py','product/config/ignored.seed']
    for name in public+excluded:
        path=tmp_path/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text('SENTINEL_ONLY_NO_ACTUAL_SECRET')
    selected=public_source_files(tmp_path)
    assert {p.relative_to(tmp_path).as_posix() for p in selected}==set(public)
    assert not any('.private' in p.parts for p in selected)

def test_actual_public_source_enumeration_has_no_private_or_build_inputs():
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]; files=public_source_files(root)
    assert root/'product/config/release-trust.json' in files
    assert root/'product/packrag/trust.py' in files
    assert all(not {'.private','build','.gradle','.cxx','.kotlin','__pycache__'}.intersection(p.relative_to(root).parts) for p in files)


def test_private_directories_are_pruned_before_scandir(tmp_path,monkeypatch):
    import os
    from pathlib import Path
    for name in ['product/.private/deep/secret.json','product/.PRIVATE/nested/secret.json',
                 'product/android/build/deep/cache.json','product/config/public.json','scripts/public.py']:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('SENTINEL_ONLY')
    original=os.scandir
    visited=[]
    def checked(path):
        parts=Path(path).relative_to(tmp_path).parts
        assert not {'.private','build'}.intersection(p.lower() for p in parts)
        visited.append(str(path));return original(path)
    monkeypatch.setattr(os,'scandir',checked)
    selected=public_source_files(tmp_path)
    assert {p.relative_to(tmp_path).as_posix() for p in selected}=={'product/config/public.json','scripts/public.py'}
    assert visited
