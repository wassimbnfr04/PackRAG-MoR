"""E3 fail-closed custody/acceptance; no missing test/visual acceptance manufactured."""
import hashlib,json,re,sys,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(values):
    for n,v in values.items():assert sha(ROOT/n)==v,n
def load(name,p):
    spec=spec_from_file_location(name,p);module=module_from_spec(spec);spec.loader.exec_module(module);return module
def originals(name,count,build,variant,android):
    run=M4/name;manifest=read(run/'instrumentation-manifest.json');saved=read(run/'collected-results.json')
    assert manifest['status']==saved['status']=='PASS' and manifest['variant']==variant
    apks={p.name:sha(p) for p in (M4/build).glob('*.apk')}
    assert manifest['apk_sha256']==saved['apk_sha256']==apks and len(saved['saved_sha256'])==count
    for n,v in saved['saved_sha256'].items():
        assert sha(run/'original-adb'/n)==v and read(run/n)==read(run/'original-adb'/n) and read(run/n)['status']=='PASS'
    for selected in manifest['selected_test_sources'].values():assert android[selected['source']]==selected['source_sha256']
    text=(run/'instrumentation.txt').read_text(encoding='utf-8');noun='test' if count==1 else 'tests'
    assert f'OK ({count} {noun})' in text and 'FAILURES' not in text
    match=re.search(r'Time:\s*([0-9][0-9\s\u00a0\u202f]*[.,][0-9]+)',text);assert match
    return dict(methods=count,original_results=count,build=build,apk_sha256=apks,
        whole_instrumentation_seconds=float(re.sub(r'\s','',match[1]).replace(',','.')))
def cases(p,count):
    row=read(p);assert row['status']=='PASS' and len(row['cases'])==count and all(c['passed'] for c in row['cases']);return row
def main():
    target=HERE/'gate.json';assert not target.exists()
    prior_path=M4/'source-details-gate-0001/gate.json';prior=read(prior_path)
    assert sha(prior_path)=='d9a5dd9b701e897bf6798026aa07e05f00613248b5a9e70d94943ee9e189e494'
    check(prior['source_sha256']);check(prior['output_sha256'])
    assert sha(ROOT/'FULL DOCUMENTATION.md')=='7c68e26003dc2debfbe4de9ce79467953fec5268c59947b93b2f2c01d612dbca'
    assert sha(ROOT/'artifacts/v1.3/architecture/architecture-v1.3.docx')=='9b02f83b186a5b7f0101add861c6ecb40f5eb0b13016f50fa0c76efc6de07536'
    history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];assert len(history)==587;check(history)
    android=read(M4/'build-0052/source-at-build-start.json')['files'];assert android==read(M4/'build-0053/source-at-build-start.json')['files'] and len(android)==574;check(android)
    preflight=read(HERE/'action-dispatch-preflight.json');assert preflight['status']=='PASS_E3_TEST_ONLY_ACTION_DISPATCH_MATCHED_PAIR_NOT_DEVICE_ACCEPTANCE'
    for build,variant in [('build-0052','debug'),('build-0053','demo')]:
        bound=next(row for row in preflight['builds'] if row['build']==build)
        assert read(M4/build/'build-result.json')['exit_code']==0 and bound['source_sha256']==android and bound['no_internet']
        assert bound['public_store_sha256']==sha(ROOT/'product/config/release-trust.json')=='2bf01e87216790babca17fd0990731cf57a3877430a9662642a0f5e0d99c87a5'
        assert bound['native_sha256']=='361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef'
        assert bound['apk_sha256']=={p.name:sha(p) for p in (M4/build).glob('*.apk')}
        suites=[ET.parse(p).getroot() for p in (M4/build/'host-tests').rglob('TEST-*.xml')]
        assert {k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']}==dict(tests=53,failures=0,errors=0,skipped=0)
    regression=read(M4/'run-0017/result-manifest.json');assert regression['status']=='PASS' and regression['totals']==dict(tests=1034,failures=0,errors=0,skipped=0)
    runtime={n:v for n,v in regression['source_sha256'].items() if n not in ['PLAN.md','STATUS.md','DECISIONS.md']};assert runtime==prior['source_sha256'] and len(runtime)==188;check(runtime)
    statuses={'first':'PASS_FIRST_INTEGRATED_DIAGNOSTIC_ITERATION_NOT_COMPLETE_E3','io':'PASS_E3_EXECUTION_AND_DIAGNOSTICS_ITERATION_NOT_COMPLETE_E3',
        'navigation':'PASS_E3_LIFECYCLE_AND_VISUAL_ITERATION_NOT_COMPLETE_E3','policy':'PASS_E3_APPROVED_NATIVE_COMPILED_POLICY_ITERATION_NOT_COMPLETE_E3'}
    for label,status in statuses.items():
        row=read(HERE/(label+'-iteration-acceptance.json'));assert row['status']==status
        for n,v in row['source_snapshots'].items():assert sha(HERE/(label+'-iteration-sources')/n)==v,n
    assert read(HERE/'retained-ui-action-dispatch-execution.json')['status']=='PASS_E3_FOUR_RETAINED_UI_ORIGINALS_NOT_COMPLETE_E3'
    assert read(HERE/'retained-ui-visual.json')['status']=='PASS_E3_RETAINED_AR_FR_CANONICAL_TESTED_VIEWPORT'
    assert read(HERE/'navigation-visual-initial.json')['status']=='FAIL_HOME_DIAGNOSTIC_MEASUREMENTS_NOT_VISIBLE_SOURCE_CANONICAL_VISIBLE'
    assert read(HERE/'navigation-visual-repaired.json')['status']=='PASS_REPAIRED_DIAGNOSTIC_AND_CANONICAL_TESTED_VIEWPORT'
    assert read(HERE/'full-background-recovered-execution.json')['status']=='PASS_E3_FULL_DEVELOPMENT_POLICY_RESTORATION_ORIGINALS_NOT_PARITY_OR_CLOSURE'
    parity=load('e3_closure_parity',HERE/'verify_full_parity_restoration_final.py').verify();saved=read(HERE/'full-parity.json')
    assert {k:v for k,v in parity.items() if k!='recorded_utc'}=={k:v for k,v in saved.items() if k!='recorded_utc'}
    phone={}
    for name,count,build,variant in [('device-ui-diagnostics-retained-0004',4,'build-0052','debug'),('device-diagnostics-full-0001',37,'build-0052','debug'),
        ('device-diagnostics-policy-full-0001',30,'build-0053','demo'),('device-development-restore-0015',1,'build-0052','debug')]:
        phone[name]=originals(name,count,build,variant,android)
    ui=M4/'device-ui-diagnostics-retained-0004';source=cases(ui/'m4-source-details-ui.json',5);languages=cases(ui/'m4-source-details-languages-ui.json',2);query=cases(ui/'m4-ui-query-controls.json',5)
    assert source['actual_weight_inference'] and query['actual_weight_inference'] and '74 °C' in query['answer'] and '[S1]' in query['answer'] and '</think>' not in query['answer']
    for row in languages['cases']:
        assert sha(ui/'original-adb'/row['screenshot'])==row['screenshot_sha256']==read(HERE/'retained-ui-visual.json')['original_png_sha256'][row['screenshot']]
    observation=read(ui/'m4-ui-query-resubmission-observation.json');assert observation==read(ui/'original-adb/m4-ui-query-resubmission-observation.json')
    assert observation['status']=='PASS_NEW_COMPLETION_EDITED_CONTEXT_ABSTENTION' and observation['previous_completion_id']!=observation['new_completion_id'] and observation['new_answer_state']=='NO_RELEVANT_EVIDENCE'
    assert sha(ui/'original-adb/m4-ui-query-resubmission-observation.json')==read(ui/'collected-resubmission-observation.json')['original_sha256']
    dev=M4/'device-diagnostics-full-0001';policy=M4/'device-diagnostics-policy-full-0001'
    guard=read(M4/'device-diagnostics-0003/m4-diagnostic-runtime.json')['owner_registry_and_model_sha256'];assert len(guard)==50
    for p in [ui/'m4-source-details-ui.json',ui/'m4-source-details-languages-ui.json',ui/'m4-ui-query-controls.json',
        dev/'m4-diagnostic-runtime.json',dev/'m4-diagnostic-lifecycle.json',dev/'m4-source-details-viewmodel.json',dev/'m4-ui-query-runtime.json',dev/'m4-ui-query-inputs.json',policy/'m4-diagnostic-policy.json']:
        row=read(p);assert row['owner_registry_and_model_sha256']==guard and row['raw_reasoning_persisted'] is False
    cases(ui/'m3-pack-management-ui.json',7);cases(dev/'m4-source-details-viewmodel.json',5);cases(dev/'m4-ui-query-runtime.json',4);cases(dev/'m4-ui-query-inputs.json',7)
    for p,n in [(policy/'m4-source-details-policy.json',2),(policy/'m4-ui-query-policy.json',3)]:assert cases(p,n)['compiled_developer_mode'] is False
    cases(M4/'device-development-restore-0015/m3-import-consent.json',4)
    # Retained0047 diagnostic-navigation is bounded by whole product APK and exact selected source equality.
    nav=read(M4/'device-ui-diagnostic-navigation-0002/instrumentation-manifest.json');assert nav['status']=='PASS'
    assert nav['apk_sha256']['app-debug.apk']==sha(M4/'build-0052/app-debug.apk')
    for row in nav['selected_test_sources'].values():assert android[row['source']]==row['source_sha256']
    capture=read(M4/'device-ui-diagnostic-navigation-0002/collected-results.json')
    for n,v in capture['saved_sha256'].items():assert sha(M4/'device-ui-diagnostic-navigation-0002/original-adb'/n)==v
    cases(M4/'device-ui-diagnostic-navigation-0002/m4-diagnostic-navigation.json',7)
    for n,row in read(HERE/'navigation-visual-repaired.json')['images'].items():
        p=M4/'device-ui-diagnostic-navigation-0002/original-adb'/n;assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
    # Failed attempts remain failures; they cannot supply fresh passing results.
    for name in ['device-diagnostics-0002','device-ui-diagnostics-retained-0001','device-ui-diagnostics-retained-0002','device-ui-diagnostics-retained-0003']:
        assert read(M4/name/'instrumentation-manifest.json')['status']=='FAIL'
    failed_suites=ET.parse(M4/'run-0016/combined-junit.xml').getroot()
    if failed_suites.tag=='testsuite':failed_suites=[failed_suites]
    assert sum(int(s.attrib.get('failures',0))+int(s.attrib.get('errors',0)) for s in failed_suites)>0
    if '--check-only' in sys.argv:print('ALL_E3_ACCEPTANCE_CHECKS_PASS_NO_CLOSURE_WRITTEN');return
    outputs={};blocked={'.private','__pycache__','build','.gradle','.cxx','.kotlin','temp','stage','runner-temp','host-temp','pytest-temp'}
    forbidden={'.apk','.pyc','.class','.jks','.key','.keystore','.pem','.seed','.seed32','.gguf','.onnx','.safetensors'}
    def capture(folder):
        for p in sorted(folder.iterdir()):
            # Exclude custody/cache/weight names BEFORE resolving/traversing/reading/hashing.
            if p.name.lower() in blocked or p.name.lower().endswith('-temp') or p.suffix.lower() in forbidden:continue
            assert p.resolve().is_relative_to(ROOT),p
            if p.is_dir():capture(p)
            elif p!=target:outputs[p.relative_to(ROOT).as_posix()]=sha(p)
    names=['diagnostics-gate-0001',*[f'build-{n:04d}' for n in range(43,54)],'run-0016','run-0017','existing-walking-smoke-0015','existing-walking-smoke-0016',
        'device-diagnostics-0001','device-diagnostics-0002','device-diagnostics-0003','device-diagnostic-lifecycle-0001',
        'device-ui-diagnostic-navigation-0001','device-ui-diagnostic-navigation-0002','device-diagnostic-policy-0001',
        'device-ui-diagnostics-retained-0001','device-ui-diagnostics-retained-0002','device-ui-diagnostics-retained-0003',*phone]
    snapshots={}
    for name in ['PLAN.md','STATUS.md','DECISIONS.md','docs/v1.3/M4E3_DIAGNOSTICS_PREPARATION.md','docs/v1.3/M4E3_METHODS.md',
        'docs/v1.3/M4E3_LIFECYCLE_CONTROLS.md','docs/v1.3/M4E3_EVIDENCE_INDEX.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md',
        'docs/v1.3/M4_INCREMENT_PLAN.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md','docs/architecture-compliance-matrix.md','docs/v1.3/M4F_ASSET_READINESS_PREPARATION.md']:
        p=HERE/'state-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes((ROOT/name).read_bytes());snapshots[name]=sha(p)
    for name in names:capture(M4/name)
    value=dict(status='M4E3_OWNED_DIAGNOSTICS_EXECUTION_LIFECYCLE_AND_UI_VERIFIED_NOT_COMPLETE_M4_OR_PRODUCT',recorded_utc=datetime.now(timezone.utc).isoformat(),
        python_tests=1034,host_methods_per_variant=53,android_inputs=574,runtime_inputs=188,source_sha256=runtime,android_source_sha256=android,
        historical_unchanged=587,prior_e2_gate_sha256=sha(prior_path),prior_e2_public_outputs_unchanged=len(prior['output_sha256']),phone=phone,
        saved_final_original_results=sum(r['original_results'] for r in phone.values()),additional_ui_ownership_original=1,retained_parity=parity,
        output_sha256=outputs,state_snapshot_sha256=snapshots,raw_reasoning_persisted=False,mobile_data_preserved=True,
        owner_models_preserved=True,owner_default_registries_preserved_within_accepted_guarded_runs=True,owner_default_registry_preserved_over_entire_e3_session=False,
        owner_exception='Failed0002 default packs/registry.sqlite bytes changed during separately observed default launcher/reverification.49 other files unchanged; no causal actor/logical-row equality proved. Accepted later guard uses explicitly documented e967 post-launch baseline.',
        failed_runs_preserved=True,retained_navigation='Actual0047 UI navigation/viewport accepted under exact selected-source/whole product APK equality; never labelled fresh0052 execution.',
        next='M4F local assets/final product audit, then software builder/evaluation/nondebuggable release/physical measurement/final documentation/three archives',
        limits=['Synthetic fixtures are not owner final content, genuine licensing/review/calibration or held-out gold','Citation format checks do not prove semantic entailment or completeness',
            'Functional timings are not M8 performance or causal hardware bottleneck measurements','Mobile data stays on; app no-INTERNET is not radio isolation','Instrumentable demo/debug-signed APK is not final nondebuggable product release'])
    target.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');print(value['status'])
if __name__=='__main__':main()
