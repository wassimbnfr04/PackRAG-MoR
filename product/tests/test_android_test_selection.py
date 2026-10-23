"""Prevent a mistyped device gate from installing/running a partial selection."""
from pathlib import Path
import pytest
from scripts.v13_test_android import selected_test_sources, build_apks
import json

BUILD = Path(__file__).resolve().parents[2] / "artifacts/v1.3/m3/build-0011"

def test_selection_is_bound_to_actual_frozen_build_inputs():
    selected = selected_test_sources(BUILD, "org.packrag.product.StrictManifestDeviceTest,org.packrag.product.StrictDatabaseDeviceTest")
    assert len(selected) == 2
    assert all(len(value["source_sha256"]) == 64 and "/src/androidTest/" in value["source"] for value in selected.values())

@pytest.mark.parametrize("selection", [
    "org.packrag.product.ManifestSchemaDeviceTest", "org.packrag.product.DatabaseValidationDeviceTest",
    "org.packrag.product.MainActivity", "", "org.packrag.product.StrictManifestDeviceTest,",
    "org.packrag.product.StrictManifestDeviceTest,org.packrag.product.StrictManifestDeviceTest",
    "org.packrag.product.StrictManifestDeviceTest#method",
])
def test_bad_device_gate_selection_rejected_before_adb(selection):
    with pytest.raises(AssertionError): selected_test_sources(BUILD, selection)

@pytest.mark.parametrize('variant',['debug','demo'])
def test_instrumentation_requires_successful_matching_artifact_pair(tmp_path,variant):
    record=tmp_path/'build-result.json'; record.write_text(json.dumps(dict(exit_code=0,variant=variant)))
    with pytest.raises(AssertionError): build_apks(tmp_path,variant)
    for name in ('app-'+variant+'.apk','app-'+variant+'-androidTest.apk'): (tmp_path/name).write_bytes(b'fixture')
    assert len(build_apks(tmp_path,variant))==2
    other='demo' if variant=='debug' else 'debug'
    with pytest.raises(AssertionError): build_apks(tmp_path,other)
    record.write_text(json.dumps(dict(exit_code=1,variant=variant)))
    with pytest.raises(AssertionError): build_apks(tmp_path,variant)

def test_legacy_debug_record_compatible_and_release_not_instrumentable(tmp_path):
    (tmp_path/'build-result.json').write_text('{"exit_code":0}')
    for name in ('app-debug.apk','app-debug-androidTest.apk'): (tmp_path/name).write_bytes(b'fixture')
    assert len(build_apks(tmp_path,'debug'))==2
    with pytest.raises(AssertionError): build_apks(tmp_path,'release')

def test_variant_preflight_failure_is_saved_without_adb(tmp_path,monkeypatch):
    import sys
    from scripts import v13_test_android as runner
    build=tmp_path/'build'; build.mkdir(); (build/'build-result.json').write_text('{"exit_code":0,"variant":"demo"}')
    run=tmp_path/'run'
    monkeypatch.setattr(sys,'argv',['runner','--serial','fixture','--build',str(build),'--run',str(run),'--variant','demo'])
    def forbidden(*args,**kwargs): raise AssertionError('Preflight failure attempted ADB')
    monkeypatch.setattr(runner.subprocess,'run',forbidden)
    with pytest.raises(AssertionError,match='APK pair missing'): runner.main()
    record=json.loads((run/'instrumentation-manifest.json').read_text())
    assert record['status']=='FAIL' and record['variant']=='demo' and record['commands']==[]
