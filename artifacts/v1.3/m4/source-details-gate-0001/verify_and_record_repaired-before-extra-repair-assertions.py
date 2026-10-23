"""Fail-closed E2 acceptance; never runs UI or manufactures missing acceptance."""
import hashlib,json,re,sys,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(values):
    for name,value in values.items():assert sha(ROOT/name)==value,name
def load(name,path):
    spec=spec_from_file_location(name,path);module=module_from_spec(spec);spec.loader.exec_module(module);return module
def main():
    target=HERE/'gate.json';assert not target.exists()
    assert read(HERE/'full-device-execution.json')['status']=='PASS_ALL_DEVELOPMENT_POLICY_AND_RESTORATION_ORIGINALS_NOT_E2_CLOSURE'
    assert read(HERE/'ui-execution-repaired.json')['status']=='PASS_FOUR_UI_METHODS_ORIGINALS_AND_SCREENSHOTS_SAVED_NOT_VISUAL_OR_E2_CLOSURE'
    assert read(HERE/'visual-inspection-repaired.json')['status']=='PASS_AR_FR_CANONICAL_DISPLAY_NOT_SEMANTIC_REVIEW'
    assert read(HERE/'short-background-audit.json')['status']=='PASS_E2_SHORT_BACKGROUND_GATES_ORIGINALS_AND_RESTORATION_NOT_UI_FULL_SUITE_OR_CLOSURE'
    assert read(HERE/'foreground-authorization.json')['status']=='OWNER_AUTHORIZED_PREPARED_E2_FOREGROUND_UI'
    preflight=read(HERE/'repaired-pair-preflight.json');assert preflight['matched_variants']
    android=read(M4/'build-0041/source-at-build-start.json')['files'];assert android==read(M4/'build-0042/source-at-build-start.json')['files'];check(android)
    assert len(android)==561
    for build in ['build-0041','build-0042']:
        assert read(M4/build/'build-result.json')['exit_code']==0
        bound=next(row for row in preflight['builds'] if row['build']==build)
        assert bound['source_sha256']==android and bound['no_internet']
        assert bound['public_store_sha256']==sha(ROOT/'product/config/release-trust.json')=='2bf01e87216790babca17fd0990731cf57a3877430a9662642a0f5e0d99c87a5'
        assert bound['native_sha256']=='361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef'
        assert bound['apk_sha256']=={p.name:sha(p) for p in (M4/build).glob('*.apk')}
        suites=[ET.parse(p).getroot() for p in (M4/build/'host-tests').rglob('TEST-*.xml')]
        assert {k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']}==dict(tests=40,failures=0,errors=0,skipped=0)
    prior_path=M4/'ui-query-gate-0002/gate.json';prior=read(prior_path)
    assert sha(prior_path)=='a275431d080e58547c2b66f2d38ff2f03fd992efbb67054ae71b4588d8701e1f';check(prior['output_sha256'])
    assert sha(ROOT/'FULL DOCUMENTATION.md')=='7c68e26003dc2debfbe4de9ce79467953fec5268c59947b93b2f2c01d612dbca'
    assert sha(ROOT/'artifacts/v1.3/architecture/architecture-v1.3.docx')=='9b02f83b186a5b7f0101add861c6ecb40f5eb0b13016f50fa0c76efc6de07536'
    history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];check(history);assert len(history)==587
    regression=read(M4/'run-0015/result-manifest.json');assert regression['status']=='PASS'
    assert regression['totals']==dict(tests=1034,failures=0,errors=0,skipped=0)
    sources={n:v for n,v in regression['source_sha256'].items() if n not in ['PLAN.md','STATUS.md','DECISIONS.md']};check(sources);assert len(sources)==188
    parity=load('e2_acceptance_retained',HERE/'verify_retained_repaired.py').verify()
    saved_parity=read(HERE/'retained-parity.json')
    assert {k:v for k,v in saved_parity.items() if k!='recorded_utc'}=={k:v for k,v in parity.items() if k!='recorded_utc'}
    phone={}
    for name,count,build,variant in [('device-ui-source-details-0002',4,'build-0041','debug'),
        ('device-source-details-full-0001',35,'build-0041','debug'),('device-source-details-policy-full-0001',29,'build-0042','demo'),
        ('device-development-restore-0013',1,'build-0041','debug')]:
        run=M4/name;manifest=read(run/'instrumentation-manifest.json');collection=read(run/'collected-results.json')
        assert manifest['status']==collection['status']=='PASS'
        apks={f'app-{variant}{suffix}.apk':sha(M4/build/f'app-{variant}{suffix}.apk') for suffix in ['', '-androidTest']}
        assert manifest['apk_sha256']==collection['apk_sha256']==apks and len(collection['saved_sha256'])==count
        for filename,value in collection['saved_sha256'].items():
            assert sha(run/'original-adb'/filename)==value and read(run/filename)==read(run/'original-adb'/filename)
            assert read(run/filename)['status']=='PASS'
        for selected in manifest['selected_test_sources'].values():assert android[selected['source']]==selected['source_sha256']
        text=(run/'instrumentation.txt').read_text(encoding='utf-8');noun='test' if count==1 else 'tests'
        assert f'OK ({count} {noun})' in text and 'FAILURES' not in text
        match=re.search(r'Time:\s*([0-9][0-9\s\u00a0\u202f]*[.,][0-9]+)',text);assert match
        phone[name]=dict(methods=count,whole_instrumentation_seconds=float(re.sub(r'\s','',match[1]).replace(',','.')),
            original_results=count,build=build,apk_sha256=apks)
    ui=M4/'device-ui-source-details-0002';record=read(ui/'m4-source-details-ui.json')
    assert record['actual_weight_inference'] and len(record['cases'])==5 and all(r['passed'] for r in record['cases'])
    languages=read(ui/'m4-source-details-languages-ui.json');assert len(languages['cases'])==2 and {r['language'] for r in languages['cases']}=={'ar','fr'}
    assert languages['owner_registry_and_model_sha256']==record['owner_registry_and_model_sha256']
    for row in languages['cases']:
        assert row['passed'] and sha(ui/'original-adb'/row['screenshot'])==row['screenshot_sha256']
        assert read(HERE/'visual-inspection-repaired.json')['image_sha256'][row['screenshot']]==row['screenshot_sha256']
    query_ui=read(ui/'m4-ui-query-controls.json');assert query_ui['actual_weight_inference'] and len(query_ui['cases'])==5 and all(r['passed'] for r in query_ui['cases'])
    assert '74 °C' in query_ui['answer'] and '[S1]' in query_ui['answer'] and '</think>' not in query_ui['answer']
    development=M4/'device-source-details-full-0001';vm=read(development/'m4-source-details-viewmodel.json')
    assert vm['actual_weight_inference'] and len(vm['cases'])==5 and all(r['passed'] for r in vm['cases'])
    runtime=read(development/'m4-ui-query-runtime.json');inputs=read(development/'m4-ui-query-inputs.json')
    assert len(runtime['cases'])==4 and len(inputs['cases'])==7 and all(r['passed'] for r in runtime['cases']+inputs['cases'])
    guards=[r['owner_registry_and_model_sha256'] for r in [record,languages,query_ui,vm,runtime,inputs]]
    assert all(g==guards[0] for g in guards)
    assert guards[0]==read(M4/'device-query-controls-0001/m4-ui-query-runtime.json')['owner_registry_and_model_sha256']
    for run in [ui,development]:
        for filename in ['m4-source-details-ui.json','m4-source-details-viewmodel.json','m4-ui-query-runtime.json','m4-ui-query-inputs.json']:
            if (run/filename).exists():assert read(run/filename)['raw_reasoning_persisted'] is False
    policy=M4/'device-source-details-policy-full-0001'
    for filename,count in [('m4-source-details-policy.json',2),('m4-ui-query-policy.json',3)]:
        value=read(policy/filename);assert value['compiled_developer_mode'] is False and len(value['cases'])==count and all(r['passed'] for r in value['cases'])
    assert len(read(M4/'device-development-restore-0013/m3-import-consent.json')['cases'])==4
    if '--check-only' in sys.argv:print('ALL_E2_ACCEPTANCE_CHECKS_PASS_NO_CLOSURE_RECORD_WRITTEN');return
    outputs={};blocked={'.private','__pycache__','build','.gradle','.cxx','.kotlin','temp','stage','runner-temp','host-temp','pytest-temp'}
    def capture(folder):
        for path in sorted(folder.iterdir()):
            if path.name in blocked or path.name.endswith('-temp'):continue
            assert path.resolve().is_relative_to(ROOT),path
            if path.is_dir():capture(path)
            elif path.suffix.lower() not in ['.apk','.pyc','.class'] and path!=target:
                assert path.suffix.lower() not in ['.jks','.key','.keystore','.pem','.seed','.seed32','.gguf','.onnx','.safetensors']
                outputs[path.relative_to(ROOT).as_posix()]=sha(path)
    names=['source-details-gate-0001','source-details-fixtures-0001','source-details-fixtures-0002','source-details-focused-0001',
        'build-0037','build-0038','build-0039','build-0040','build-0041','build-0042','device-ui-source-details-0001','run-0015','existing-walking-smoke-0014','conflict-smoke-0008',
        'relevance-smoke-0005','representation-smoke-0005','source-text-smoke-0003','selection-smoke-0003',
        'device-source-details-0001','device-source-details-policy-0001','device-development-restore-0012','device-development-restore-0014',*phone]
    snapshots={}
    for name in ['PLAN.md','STATUS.md','DECISIONS.md','docs/v1.3/M4E2_METHODS.md','docs/v1.3/M4E2_SOURCE_PREPARATION.md',
        'docs/v1.3/M4_INCREMENT_PLAN.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md','docs/architecture-compliance-matrix.md']:
        saved=HERE/'state-snapshot'/name;saved.parent.mkdir(parents=True,exist_ok=True);assert not saved.exists();saved.write_bytes((ROOT/name).read_bytes());snapshots[name]=sha(saved)
    for name in names:capture(M4/name)
    record=dict(status='M4E2_CAPTURED_SOURCE_AND_VERIFIED_PACK_DETAILS_VERIFIED_NOT_COMPLETE_M4_OR_PRODUCT',recorded_utc=datetime.now(timezone.utc).isoformat(),
        python_tests=1034,host_methods_per_variant=40,android_inputs=len(android),runtime_inputs=len(sources),source_sha256=sources,android_source_sha256=android,
        historical_unchanged=len(history),prior_e1_gate_sha256=sha(prior_path),prior_e1_public_outputs_unchanged=len(prior['output_sha256']),
        phone=phone,saved_final_original_results=sum(r['original_results'] for r in phone.values()),retained_parity=parity,
        signed_source_scope=dict(packs=17,active_inactive_inspections_per_variant=34,public_source_rows_per_variant=43,fields_per_row=19,rejection_controls_per_variant=11),
        output_sha256=outputs,state_snapshot_sha256=snapshots,raw_reasoning_persisted=False,mobile_data_preserved=True,owner_models_and_default_registries_preserved=True,
        failed_runs_preserved=True,next='M4E3 diagnostics/lifecycle/accessibility, then F assets, software evaluation, release and three-archive delivery',
        limits=['Synthetic software fixtures are not owner final content or genuine licensing/review/calibration/gold',
            'Structural citation checks are not semantic entailment/completeness proof','AR/FR screenshots exercise actual viewer component, not new inference or app admission of fixture keys',
            'Functional times are not M8 performance/thermal/bottleneck measurements','Demo debug signed/instrumentable, not final nondebuggable product release'])
    target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
if __name__=='__main__':main()
