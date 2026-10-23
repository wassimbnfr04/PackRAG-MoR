"""Fail-closed F1 acceptance only after every actual gate; never synthesize missing results."""
import hashlib,json,re,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def check(mapping):
    for name,value in mapping.items():assert sha(ROOT/name)==value,name
def main():
    target=HERE/'gate.json';assert not target.exists()
    e3_path=M4/'diagnostics-gate-0001/gate.json';e3=read(e3_path)
    assert sha(e3_path)=='683272dc411f8065ea8fc8811475f74348ab741a9b7f0c726524bea14f5ed702'
    check(e3['source_sha256']);check(e3['output_sha256'])
    history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];assert len(history)==587;check(history)
    assert sha(ROOT/'FULL DOCUMENTATION.md')=='7c68e26003dc2debfbe4de9ce79467953fec5268c59947b93b2f2c01d612dbca'
    assert sha(ROOT/'artifacts/v1.3/architecture/architecture-v1.3.docx')=='9b02f83b186a5b7f0101add861c6ecb40f5eb0b13016f50fa0c76efc6de07536'
    pair=read(HERE/'corrected-pair-preflight.json');assert pair['status']=='PASS_CORRECTED_F1_MATCHED_HOST_PAIR_NOT_DEVICE_ACCEPTANCE'
    inputs=read(M4/'build-0056/source-at-build-start.json')['files'];assert inputs==read(M4/'build-0057/source-at-build-start.json')['files']
    assert len(inputs)==579 and read(HERE/'current-source-at-closure.json')['files']==inputs;check(inputs)
    for build,variant in [('build-0056','debug'),('build-0057','demo')]:
        host=read(HERE/(build+'-host-capture.json'));assert host['host_totals']==dict(tests=62,failures=0,errors=0,skipped=0)
        assert host['variant']==variant
        for name,value in host['apk_sha256'].items():assert sha(M4/build/name)==value
        with zipfile.ZipFile(M4/build/('app-'+variant+'.apk')) as archive:
            native=archive.read('lib/arm64-v8a/libpackrag_jni.so')
            assert len(native)==5597496 and hashlib.sha256(native).hexdigest()=='361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef'
    pre_launch=read(M4/'device-diagnostics-0003/m4-diagnostic-runtime.json')['owner_registry_and_model_sha256'];assert len(pre_launch)==50
    failure=read(HERE/'adjacent-terminal-guard-diagnosis.json')
    assert failure['status']=='FAIL_ADJACENT_OWNER_REGISTRY_BYTES_CHANGED_FOUR_METHOD_ORIGINALS_PRESERVED'
    assert failure['methods']==5 and failure['failures']==1 and failure['before_sha256']==pre_launch
    baseline=failure['after_sha256'];assert set(baseline)==set(pre_launch) and len(baseline)==50
    delta={name:dict(before=pre_launch[name],after=baseline[name]) for name in baseline if baseline[name]!=pre_launch[name]}
    assert delta==failure['differences']=={'packs/registry.sqlite':dict(before='e967352d73a4d69777f8030e2f4a8578347bd667861ba7b0a0f3775ecaae4a81',after='cf140bbf898aea7eb194406fa440e916cd2d746bb77b222a7c447f3f0e28ed10')}
    failed=M4/'device-local-assets-adjacent-0001'
    failed_manifest=read(failed/'instrumentation-manifest.json')
    assert failed_manifest['status']=='FAIL' and failed_manifest['apk_sha256']==pair['apk_sha256']['build-0056']
    failed_text=(failed/'instrumentation.txt').read_text(encoding='utf-8').replace('\r','')
    assert 'Tests run: 5,  Failures: 1' in failed_text
    assert set(failure['passing_original_sha256'])=={'m4-diagnostic-runtime.json','m4-diagnostic-lifecycle.json','m4-ui-query-inputs.json','m4-source-details-viewmodel.json'}
    for name,value in failure['passing_original_sha256'].items():
        p=failed/'partial-collected-results'/name;assert sha(p)==value and read(p)['status']=='PASS'
        expected=pre_launch if name in {'m4-diagnostic-runtime.json','m4-diagnostic-lifecycle.json'} else baseline
        assert read(p)['owner_registry_and_model_sha256']==failure['passing_method_guards'][name]==expected
    stale=failure['failed_method_phone_file'];assert stale['new_result_accepted'] is False and stale['parsed_equal_to_prior_e3'] is True
    assert sha(ROOT/stale['file'])==stale['sha256']
    assert read(ROOT/stale['file'])==read(M4/'device-diagnostics-full-0001/original-adb/m4-ui-query-runtime.json')
    preparation=read(HERE/'guarded-retry-preparation.json')
    assert preparation['status']=='PASS_UNCHANGED_TEST_RETRY_PREPARATION_POST_LAUNCH_BASELINE_NOT_TEST_ACCEPTANCE'
    assert preparation['owner_public_file_sha256']==baseline and preparation['target_app_closed_after_all_current_tests_finished'] is True
    assert preparation['current_default_registry_sha256']==sha(HERE/'default-registry-post-change.sqlite')==baseline['packs/registry.sqlite']
    assert preparation['current_default_registry_read_only_integrity']=='ok'
    policy_sidecar=read(HERE/'policy-schema-and-owner-guard-0001.json')
    assert policy_sidecar['status']=='PASS_ACTUAL_POLICY_PHASE_FINAL_OWNER_GUARD_AND_UNCHANGED_LEGACY_SCHEMA_NOT_CLOSURE'
    assert policy_sidecar['owner_public_file_sha256']==baseline and policy_sidecar['guarded_file_count']==50
    assert all(row['returncode']==0 for row in policy_sidecar['commands'])
    assert read(HERE/'policy-and-restoration-execution-0001.json')['status']=='FAIL'
    assert policy_sidecar['failed_driver_sha256']==sha(HERE/'policy-and-restoration-execution-0001.json')
    assert policy_sidecar['failed_checker_source_sha256']==sha(HERE/'verify-background-first-policy-attempt.py.txt')
    assert policy_sidecar['actual_failure_stderr_sha256']==sha(HERE/'policy-restoration-0001-stage-3.stderr.txt')
    runs=[]
    for name,phase,variant,count in [('device-local-assets-0002','core','debug',3),('device-local-assets-adjacent-0002','adjacent','debug',5),
        ('device-local-assets-policy-0001','core','demo',3),('device-local-assets-policy-adjacent-0001','adjacent','demo',3)]:
        verified=read(HERE/(name+'-verified.json'))
        assert verified['status']=='PASS_F1_'+phase.upper()+'_INDEPENDENT_ORIGINAL_CONTRACT_CHECK_NOT_CLOSURE'
        expected_baseline=pre_launch if name=='device-local-assets-0002' else baseline
        assert verified['methods']==count and verified['variant']==variant and verified['owner_public_file_sha256']==expected_baseline
        assert verified['execution_sha256']==sha(HERE/(name+'-execution.json'))
        execution=read(HERE/(name+'-execution.json'));selected='build-0056' if variant=='debug' else 'build-0057'
        assert execution['status']=='PASS_F1_'+phase.upper()+'_ACTUAL_ORIGINALS_NOT_FULL_F1'
        assert execution['build']==selected and execution['variant']==variant and execution['phase']==phase
        assert all(row['returncode']==0 for row in execution['commands'])
        manifest=read(M4/name/'instrumentation-manifest.json')
        collection=read(M4/name/'collected-results.json');assert len(collection['saved_sha256'])==count
        assert manifest['status']==collection['status']=='PASS' and manifest['variant']==variant
        assert manifest['apk_sha256']==collection['apk_sha256']==pair['apk_sha256'][selected]
        assert execution['original_sha256']==collection['saved_sha256']
        assert execution['instrumentation_sha256']==sha(M4/name/'instrumentation-manifest.json')
        assert execution['collection_sha256']==sha(M4/name/'collected-results.json')
        assert set(verified['observations'])==set(collection['saved_sha256'])
        for original,value in collection['saved_sha256'].items():
            assert sha(M4/name/'original-adb'/original)==value
            assert verified['observations'][original]['original_sha256']==value
            assert read(M4/name/original)==read(M4/name/'original-adb'/original)
            data=read(M4/name/original)
            assert data['status']=='PASS'
            assert all(row['passed'] is True for row in data['cases'])
            schema=policy_sidecar['legacy_report_contracts'].get(original) if name=='device-local-assets-policy-adjacent-0001' else None
            if schema:
                assert schema['original_sha256']==value and sorted(data)==schema['exact_key_set']
                assert sha(ROOT/schema['test_source'])==schema['test_source_sha256']==e3['android_source_sha256'][schema['test_source']]
                assert 'owner_registry_and_model_sha256' not in data and data['compiled_developer_mode'] is False
                assert verified['legacy_policy_guard_sidecar_sha256']==sha(HERE/'policy-schema-and-owner-guard-0001.json')
                if schema['missing_network_mode']:assert original=='m4-source-details-policy.json' and 'network_mode' not in data
                else:assert data['network_mode']=='MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET'
            else:
                assert data['owner_registry_and_model_sha256']==expected_baseline
                assert data['network_mode']=='MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET'
        runs.append(verified)
    for variant,name,prior in [('debug','device-local-assets-adjacent-0002','device-diagnostics-full-0001'),('demo','device-local-assets-policy-adjacent-0001','device-diagnostics-policy-full-0001')]:
        verified=read(HERE/(name+'-verified.json'))
        for original,observation in verified['observations'].items():
            previous=M4/prior/'original-adb'/original
            assert sha(previous)==e3['output_sha256'][previous.relative_to(ROOT).as_posix()]
            assert [row['id'] for row in read(previous)['cases']]==[row['id'] for row in read(M4/name/'original-adb'/original)['cases']]
    # No old positive may be promoted after a failed fixture setup.
    assert read(M4/'device-local-assets-0001/instrumentation-manifest.json')['status']=='FAIL'
    assert read(HERE/'hardlink-setup-failure.json')['status'].startswith('FAIL_TWO_ACTUAL_HARDLINK')
    partial=M4/'device-local-assets-0001/partial-collected-results/m4-local-assets-negative.json'
    assert sha(partial)==read(HERE/'hardlink-setup-failure.json')['partial_original']['sha256']
    assert read(partial)['owner_registry_and_model_sha256']==pre_launch
    ui=M4/'device-local-assets-ui-0001';manifest=read(ui/'instrumentation-manifest.json');collection=read(ui/'collected-results.json')
    assert manifest['status']==collection['status']=='PASS' and manifest['variant']=='debug'
    assert manifest['apk_sha256']==collection['apk_sha256']==pair['apk_sha256']['build-0056']
    text=(ui/'instrumentation.txt').read_text(encoding='utf-8');assert 'OK (1 test)' in text and 'FAILURES' not in text
    assert len(collection['saved_sha256'])==1
    original=ui/'original-adb/m4-local-assets-ui.json';assert sha(original)==collection['saved_sha256']['m4-local-assets-ui.json']
    value=read(original);assert value==read(ui/'m4-local-assets-ui.json') and value['status']=='PASS'
    assert len(value['cases'])==5 and all(row['passed'] is True for row in value['cases'])
    assert value['owner_registry_and_model_sha256']==baseline and value['guards_unchanged'] and value['actual_weight_inference']
    assert value['network_mode']=='MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET'
    assert value['raw_reasoning_persisted'] is False and '74 °C' in value['answer'] and '[S1]' in value['answer']
    visual=read(HERE/'ui-visual-0001.json');assert visual['status']=='PASS_F1_ORIGINAL_ASSET_SCREEN_TESTED_VIEWPORT'
    for name,identity in value['visual_png'].items():
        assert sha(ui/'original-adb'/name)==identity['sha256']==visual['original_png_sha256'][name]
        assert (ui/'original-adb'/name).stat().st_size==identity['bytes']
    # Actual restored development product and original consent result, never an old run.
    restored=M4/'device-local-assets-development-restore-0001'
    restore=read(restored/'instrumentation-manifest.json');saved=read(restored/'collected-results.json')
    assert restore['status']==saved['status']=='PASS' and restore['variant']=='debug'
    assert restore['apk_sha256']==saved['apk_sha256']==pair['apk_sha256']['build-0056']
    assert set(saved['saved_sha256'])=={'m3-import-consent.json'}
    assert sha(restored/'original-adb/m3-import-consent.json')==saved['saved_sha256']['m3-import-consent.json']
    consent=read(restored/'original-adb/m3-import-consent.json');assert consent==read(restored/'m3-import-consent.json') and consent['status']=='PASS'
    assert len(consent['cases'])==4 and all(row['passed'] for row in consent['cases'])
    final_owner=read(HERE/'owner-at-closure.json')
    assert final_owner['status']=='PASS_KNOWN_PUBLIC_OWNER_FILES_MATCH_POST_LAUNCH_BASELINE_NOT_WHOLE_SESSION_PRESERVATION'
    assert final_owner['owner_public_file_sha256']==baseline and final_owner['guarded_file_count']==50
    assert final_owner['whole_f1_session_default_registry_bytes_preserved'] is False
    assert all(row['returncode']==0 for row in final_owner['commands'])
    assert final_owner['restored_manifest_sha256']==sha(restored/'instrumentation-manifest.json')
    assert final_owner['retry_preparation_sha256']==sha(HERE/'guarded-retry-preparation.json')
    if '--check-only' in sys.argv:print('ALL_F1_ACCEPTANCE_CHECKS_PASS_NO_CLOSURE_WRITTEN');return
    blocked={'.private','__pycache__','build','.gradle','.cxx','.kotlin','temp','stage','runner-temp','host-temp','pytest-temp'}
    forbidden={'.apk','.pyc','.class','.jks','.key','.keystore','.pem','.seed','.seed32','.gguf','.onnx','.safetensors'}
    outputs={}
    def capture(folder):
        for p in sorted(folder.iterdir()):
            if p.name.lower() in blocked or p.name.lower().endswith('-temp') or p.suffix.lower() in forbidden:continue
            assert not p.is_symlink(),p
            if p.is_dir():capture(p)
            elif p.is_file():outputs[p.relative_to(ROOT).as_posix()]=sha(p)
    for folder in [HERE,M4/'asset-readiness-pause-0001',M4/'device-local-assets-0001',failed,*[M4/row['run'] for row in runs],ui,restored,*[M4/('build-'+n) for n in ['0054','0055','0056','0057']]]:capture(folder)
    for name in ['docs/v1.3/M4F1_ASSET_CONTRACT.md','docs/v1.3/M4F1_DEVICE_VALIDATION.md','docs/v1.3/M4F1_EVIDENCE_INDEX.md','docs/v1.3/M4F2_IMPORT_ACCEPTANCE_PREPARATION.md']:
        outputs[name]=sha(ROOT/name)
    record=dict(status='M4F1_LOCAL_ASSET_READINESS_NATIVE_RECOVERY_AND_UI_VERIFIED_NOT_FULL_M4_OR_PRODUCT',recorded_utc=datetime.now(timezone.utc).isoformat(),
        prior_e3_gate_sha256=sha(e3_path),prior_e3_outputs_unchanged=len(e3['output_sha256']),historical_unchanged=587,
        retained_python_tests=1034,python_scope='Explicitly retained E3 run0017 under identical188 Python-runtime inputs; no fresh Python run claimed at F1. Fresh full run required at F4.',
        source_sha256=e3['source_sha256'],android_source_sha256=inputs,host_methods_per_variant=62,phone_runs=runs,ui_methods=1,restored_consent_methods=1,
        saved_final_method_originals=16,retained_adjacent_case_id_parity=True,owner_public_file_sha256=baseline,pre_launch_owner_public_file_sha256=pre_launch,
        policy_legacy_report_guard_scope='QueryControlsPolicy and SourceDetailsPolicy originals omit per-method owner hashes; actual unchanged schemas are retained, with matching DiagnosticPolicy and independent known50-file post-phase sidecar before restoration. SourceDetailsPolicy also omits network metadata; compiled APK no-INTERNET identity remains independently required.',
        whole_f1_session_default_registry_bytes_preserved=False,owner_exception=dict(differences=delta,
            failed_run='device-local-assets-adjacent-0001',accepted_retry='device-local-assets-adjacent-0002',
            diagnosis_sha256=sha(HERE/'adjacent-terminal-guard-diagnosis.json'),retry_preparation_sha256=sha(HERE/'guarded-retry-preparation.json'),
            scope='Only later accepted runs preserve the post-launch baseline. Core development0002 used the pre-launch baseline. The whole session failed default-registry byte preservation. Current DB integrity does not establish before/after logical equivalence or causal actor; old DB bytes unavailable.'),
        prior_e3_owner_registry_exception_retained=e3['owner_exception'],
        output_sha256=outputs,raw_reasoning_persisted=False,mobile_data_preserved=True,
        limits='F1 only: synthetic functional/software contracts, no real domain expertise/calibration/license approval/held-out gold, no causal hardware bottleneck or performance benchmark, no radio isolation, no final nondebuggable release. First hardlink and adjacent owner-registry failures0001 remain immutable. Whole-session default registry byte preservation failed; accepted retry uses explicitly post-launch baseline. F2/F3/F4 and later software/release/delivery remain.',
        next='Checkpoint exact tested public source/evidence/documents, then F2 local URI import under its independent preparation.')
    target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
if __name__=='__main__':main()
