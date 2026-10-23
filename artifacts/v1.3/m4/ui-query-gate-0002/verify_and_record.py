"""Fail-closed E1 closure after actual UI/new/retained/policy/restoration gates."""
import hashlib,json,re,sys
from datetime import datetime,timezone
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(values):
    for name,value in values.items():assert digest(ROOT/name)==value,name
def load(name,path):
    spec=spec_from_file_location(name,path);module=module_from_spec(spec);spec.loader.exec_module(module);return module
def main():
    target=HERE/'gate.json';assert not target.exists()
    assert read(HERE/'device-execution.json')['status']=='PASS_NEW_RETAINED_POLICY_RESTORED_ORIGINALS_NOT_E1_CLOSURE'
    assert read(HERE/'ui-execution-0003.json')['status']=='PASS_TWO_FOREGROUND_METHODS_ORIGINALS_SAVED'
    assert read(HERE/'regression-execution.json')['status']=='PASS_FULL_PYTHON_AND_RETAINED_DESKTOP_WALKING'
    assert read(HERE/'test-only-repair-proof.json')['status'].startswith('PASS_EXACT_TEST_SCROLL_REPAIR_')
    preflight=read(HERE/'preflight-repaired.json');assert preflight['status'].startswith('PASS_')
    android=read(M4/'build-0035/source-at-build-start.json')['files'];assert android==read(M4/'build-0036/source-at-build-start.json')['files'];check(android)
    assert len(android)==548
    prior_path=M4/'selection-gate-0002/gate.json';prior=read(prior_path);check(prior['output_sha256']);check(prior['source_sha256'])
    python=read(M4/'run-0014/result-manifest.json');assert python['status']=='PASS' and python['totals']==dict(tests=1010,failures=0,errors=0,skipped=0)
    sources={n:v for n,v in python['source_sha256'].items() if n not in ['PLAN.md','STATUS.md','DECISIONS.md']};assert sources==prior['source_sha256'];check(sources)
    smoke=read(M4/'existing-walking-smoke-0013/smoke-results.json');assert smoke['status']=='PASS' and len(smoke['cases'])==14
    assert read(M4/'existing-walking-smoke-0013/inputs.json')['source_sha256']==sources
    history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];check(history)
    assert digest(ROOT/'FULL DOCUMENTATION.md')=='7c68e26003dc2debfbe4de9ce79467953fec5268c59947b93b2f2c01d612dbca'
    assert digest(ROOT/'artifacts/v1.3/architecture/architecture-v1.3.docx')=='9b02f83b186a5b7f0101add861c6ecb40f5eb0b13016f50fa0c76efc6de07536'
    parity=load('e1_retained_parity',HERE/'verify_retained.py').verify()
    phone={}
    for name,count,build,variant in [
        ('device-ui-query-0003',2,'build-0035','debug'),('device-query-controls-0001',2,'build-0035','debug'),
        ('device-query-regression-0001',30,'build-0035','debug'),('device-query-policy-0001',26,'build-0036','demo'),
        ('device-development-restore-0011',1,'build-0035','debug')]:
        run=M4/name;manifest=read(run/'instrumentation-manifest.json');collection=read(run/'collected-results.json')
        assert manifest['status']==collection['status']=='PASS'
        apks={f'app-{variant}{suffix}.apk':digest(M4/build/f'app-{variant}{suffix}.apk') for suffix in ['','-androidTest']}
        assert manifest['apk_sha256']==collection['apk_sha256']==apks
        assert len(collection['saved_sha256'])==count
        for filename,value in collection['saved_sha256'].items():
            assert digest(run/'original-adb'/filename)==value
            parsed=read(run/'original-adb'/filename);assert parsed==read(run/filename) and parsed['status']=='PASS'
        for selected in manifest['selected_test_sources'].values():assert android[selected['source']]==selected['source_sha256']
        text=(run/'instrumentation.txt').read_text(encoding='utf-8');noun='test' if count==1 else 'tests'
        assert f'OK ({count} {noun})' in text and 'FAILURES' not in text
        match=re.search(r'Time:\s*([0-9][0-9\s\u00a0\u202f]*[.,][0-9]+)',text);assert match
        phone[name]=dict(methods=count,whole_instrumentation_seconds=float(re.sub(r'\s','',match[1]).replace(',','.')),build=build,
            apk_sha256=apks,original_results=len(collection['saved_sha256']))
    ui=read(M4/'device-ui-query-0003/m4-ui-query-controls.json');runtime=read(M4/'device-query-controls-0001/m4-ui-query-runtime.json');inputs=read(M4/'device-query-controls-0001/m4-ui-query-inputs.json')
    assert ui['actual_weight_inference'] and len(ui['cases'])==5 and all(c['passed'] for c in ui['cases'])
    assert ui['as_of']=='2027-01-01' and ui['current_law'] and '74 °C' in ui['answer'] and '[S1]' in ui['answer'] and '</think>' not in ui['answer']
    assert len(runtime['cases'])==4 and len(inputs['cases'])==7 and all(c['passed'] for c in runtime['cases']+inputs['cases'])
    assert ui['owner_registry_and_model_sha256']==runtime['owner_registry_and_model_sha256']==inputs['owner_registry_and_model_sha256']
    supported=runtime['cases'][0];assert supported['state']=='ANSWER_ACCEPTED' and supported['as_of']=='2027-01-01' and supported['jurisdiction'] is None and supported['current_law']
    assert supported['canonical_sha256']=='266af80f5d4da1dac500acd9a2bcc1fd2317b2caf49141ebb586280b9df49333'
    assert supported['manifest_sha256']=='63d9e7686e03dc0bea9d3dbf190c193432fe9f3b126fc5e54eb505d90c5a4215'
    assert (supported['prefill_tokens'],supported['evidence_tokens'])==(428,256)
    assert 1<=supported['emitted_tokens']<=512
    policy=read(M4/'device-query-policy-0001/m4-ui-query-policy.json');assert not policy['compiled_developer_mode'] and len(policy['cases'])==3 and all(c['passed'] for c in policy['cases'])
    assert len(read(M4/'device-development-restore-0011/m3-import-consent.json')['cases'])==4
    if '--check-only' in sys.argv:print('ALL_E1_ACCEPTANCE_CHECKS_PASS_NO_CLOSURE_RECORD_WRITTEN');return
    snapshots={}
    for name in ['PLAN.md','STATUS.md','DECISIONS.md']:
        saved=HERE/'state-snapshot'/name;saved.parent.mkdir(parents=True,exist_ok=True);assert not saved.exists();saved.write_bytes((ROOT/name).read_bytes());snapshots[name]=digest(saved)
    names=['ui-query-resume-0001','ui-query-gate-0001','ui-query-gate-0002','run-0013','run-0014','existing-walking-smoke-0013',
        'build-0032','build-0033','build-0034','build-0035','build-0036','device-ui-query-0001','device-ui-query-0002','device-ui-query-0003',
        'device-query-controls-0001','device-query-regression-0001','device-query-policy-0001','device-development-restore-0011']
    blocked={'.private','__pycache__','build','.gradle','.cxx','.kotlin','temp','stage','runner-temp','host-temp'};outputs={}
    def capture(folder):
        for p in sorted(folder.iterdir()):
            if p.name in blocked or p.name.endswith('-temp'):continue
            assert p.resolve().is_relative_to(ROOT),p
            if p.is_dir():capture(p)
            elif p.suffix not in ['.apk','.pyc','.class'] and p!=target:
                assert p.suffix.lower() not in ['.jks','.key','.keystore','.pem','.seed','.seed32']
                outputs[p.relative_to(ROOT).as_posix()]=digest(p)
    for name in names:capture(M4/name)
    for name in ['docs/v1.3/M4E1_METHODS.md','docs/v1.3/M4E2_SOURCE_PREPARATION.md']:
        # Documentation is versioned with the gate; later live edits must not mutate this bound copy.
        saved=HERE/'documentation-snapshot'/Path(name).name;saved.parent.mkdir(parents=True,exist_ok=True);assert not saved.exists();saved.write_bytes((ROOT/name).read_bytes());outputs[saved.relative_to(ROOT).as_posix()]=digest(saved)
    record=dict(status='M4E1_QUERY_CONTROLS_CAPTURED_CONTEXT_VERIFIED_NOT_COMPLETE_M4_OR_PRODUCT',recorded_utc=datetime.now(timezone.utc).isoformat(),
        python_tests=1010,host_methods_per_variant=37,android_inputs=len(android),runtime_inputs=len(sources),historical_unchanged=len(history),
        prior_d3_gate_sha256=digest(prior_path),prior_d3_public_outputs_unchanged=len(prior['output_sha256']),phone=phone,
        saved_final_original_results=sum(r['original_results'] for r in phone.values()),retained_parity=parity,
        source_sha256=sources,android_source_sha256=android,output_sha256=outputs,state_snapshot_sha256=snapshots,
        repaired_ui_scope=read(HERE/'test-only-repair-proof.json'),initial_failures_preserved=True,
        raw_reasoning_persisted=False,mobile_data_preserved=True,owner_models_and_default_registries_preserved=True,
        next='M4E2 source/pack details, then E3 diagnostics/lifecycle, F assets, software evaluation and final release/delivery',
        limits=['Synthetic software fixtures, not owner final content/legal review/calibration/gold','Structural citations are not entailment/completeness proof',
            'Functional timings are not M8 performance/thermal/bottleneck or foreground/background comparisons','Demo is debug signed/instrumentable, not final nondebuggable product release'])
    target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
if __name__=='__main__':main()
