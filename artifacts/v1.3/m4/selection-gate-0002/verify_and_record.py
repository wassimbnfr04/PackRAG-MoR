"""Additive D3 closure after all retained and new physical gates, never compile-only."""
import hashlib,json,re,subprocess,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
sys.path.insert(0,str(ROOT))
from scripts.v13_result_manifest import public_source_files
from product.packrag.config import file_sha
from importlib.util import spec_from_file_location,module_from_spec
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def check(values):
    for name,value in values.items():assert file_sha(ROOT/name)==value,name
def load_selection():
    spec=spec_from_file_location('d3_selection_parity',HERE/'verify_selection.py');module=module_from_spec(spec);spec.loader.exec_module(module);return module
def main():
    target=HERE/'gate.json';assert not target.exists()
    command=[sys.executable,'-X','utf8',str(HERE/'retained_checks.py'),'--check-only']
    completed=subprocess.run(command,cwd=ROOT,capture_output=True)
    assert completed.returncode==0,completed.stderr.decode(errors='replace')
    assert b'ALL_RETAINED_D3_BASELINE_CHECKS_PASS_NO_CLOSURE_RECORD_WRITTEN' in completed.stdout
    prior=read(M4/'representation-gate-0002/gate.json');check(prior['output_sha256'])
    assert file_sha(ROOT/'FULL DOCUMENTATION.md')=='7c68e26003dc2debfbe4de9ce79467953fec5268c59947b93b2f2c01d612dbca'
    assert file_sha(ROOT/'artifacts/v1.3/architecture/architecture-v1.3.docx')=='9b02f83b186a5b7f0101add861c6ecb40f5eb0b13016f50fa0c76efc6de07536'
    history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];check(history)
    python=read(M4/'run-0012/result-manifest.json');assert python['status']=='PASS' and python['totals']==dict(tests=1010,failures=0,errors=0,skipped=0)
    sources={k:v for k,v in python['source_sha256'].items() if k not in ('PLAN.md','STATUS.md','DECISIONS.md')};check(sources)
    assert set(sources)=={p.relative_to(ROOT).as_posix() for p in public_source_files(ROOT)}
    assert read(M4/'selection-iteration-0002/result.json')['sources_unchanged']==len(sources)==185
    smoke=read(M4/'selection-smoke-0002/selection-smoke-results.json');assert smoke['status']=='PASS' and len(smoke['cases'])==8 and smoke['tokenizer_cases']==8
    assert read(M4/'selection-smoke-0002/inputs.json')['source_sha256']==sources
    original=read(M4/'selection-smoke-0001/atomic-last-runtime-observed.json')
    assert original['expected_state']=='ANSWER_ACCEPTED' and original['result']['state']=='OUTPUT_REJECTED' and original['result']['rejection_reason']=='uncited_paragraph'
    assert read(M4/'device-selection-0001/instrumentation-manifest.json')['status']=='FAIL'
    assert read(M4/'device-selection-full-0001/instrumentation-manifest.json')['status']=='FAIL'
    fixture=read(M4/'selection-fixtures-0002/cases.json');assert len(fixture['packs'])==len(fixture['cases'])==8
    for filename,key in [('fixed-expectations.json','fixed_expectations_sha256'),('independent-ranks.json','independent_ranks_sha256'),('embedding-inputs.json','embedding_inputs_sha256'),('public-key.raw','public_key_sha256')]:assert file_sha(M4/'selection-fixtures-0002'/filename)==fixture[key]
    for filename,key in [('scripts/v13_selection_fixtures.py','script_sha256'),('scripts/v13_query_identifier_fixtures.py','builder_sha256'),('product/tests/fixtures/selection-contracts.json','fixed_contract_sha256')]:assert file_sha(ROOT/filename)==fixture[key]
    assets=ROOT/'product/android/app/src/androidTest/assets/selection-corpus'
    assert file_sha(assets/'cases.json')==file_sha(M4/'selection-fixtures-0002/cases.json')
    assert file_sha(assets/'selection-contracts.json')==fixture['fixed_contract_sha256']
    for row in fixture['packs']:assert file_sha(assets/row['filename'])==row['sha256']==file_sha(M4/'selection-fixtures-0002'/row['filename'])
    format=read(M4/'selection-format-reference-0001/case.json')
    assert format['scope']=='POST_OBSERVATION_FORMAT_CONTROL_NOT_HELDOUT_GOLD'
    assert format['script_sha256']==file_sha(ROOT/'scripts/v13_selection_format_reference.py')
    assert format['diagnostic_sha256']==file_sha(M4/'selection-output-diagnostic-0001/observed.json')
    assert file_sha(assets/'format-control.json')==file_sha(M4/'selection-format-reference-0001/case.json')
    android=read(M4/'build-0028/source-at-build-start.json')['files'];check(android)
    assert android==read(M4/'build-0029/source-at-build-start.json')['files'] and len(android)==543
    for build,variant in [('build-0028','debug'),('build-0029','demo')]:
        with zipfile.ZipFile(M4/build/f'app-{variant}-androidTest.apk') as archive:
            for path in assets.iterdir():assert hashlib.sha256(archive.read('assets/selection-corpus/'+path.name)).hexdigest()==file_sha(path)
    selection=load_selection();phone={}
    for run,methods,build in [('device-selection-full-0002',30,'build-0028'),('device-production-selection-0001',25,'build-0029')]:
        parity=selection.verify(M4/run);manifest=read(M4/run/'instrumentation-manifest.json')
        text=(M4/run/'instrumentation.txt').read_text();assert f'OK ({methods} tests)' in text
        match=re.search(r'Time:\s*([0-9][0-9\s\u00a0\u202f]*[.,][0-9]+)',text);assert match
        phone[run]=dict(methods=methods,whole_instrumentation_seconds=float(re.sub(r'\s','',match[1]).replace(',','.')),build=build,
            apk_sha256=manifest['apk_sha256'],retained_exact_tokenizer_cases=43,retained_runtime_states=19,selection=parity,
            saved_original_results=len(read(M4/run/'collected-results.json')['saved_sha256']))
    restored=M4/'device-development-restore-0010';collection=read(restored/'collected-results.json');assert collection['status']=='PASS'
    for name,value in collection['saved_sha256'].items():assert file_sha(restored/'original-adb'/name)==value and read(restored/name)==read(restored/'original-adb'/name)
    assert read(restored/'instrumentation-manifest.json')['apk_sha256']==phone['device-selection-full-0002']['apk_sha256']
    if '--check-only' in sys.argv:
        print('ALL_D3_ACCEPTANCE_CHECKS_PASS_NO_CLOSURE_RECORD_WRITTEN');return
    # Explicit owned public roots: no cache/temp traversal or private custody.
    names=['selection-pure-0001','selection-adjacent-0001','selection-iteration-0001','selection-walking-0001','run-0011',
        'ownership-adjacent-0001','ownership-adjacent-0002','ownership-adjacent-0003','build-0022','build-0023','build-0024','build-0025','build-0026','build-0027','build-0028','build-0029',
        'device-selection-intermediate-0001','selection-fixtures-0001','selection-boundary-diagnostic-0001','selection-fixtures-0002','selection-signed-adjacent-0001',
        'selection-smoke-0001','selection-output-diagnostic-0001','selection-format-reference-0001','selection-smoke-0002','selection-focused-0001',
        'selection-iteration-0002','run-0012','selection-walking-0002','device-selection-0001','device-selection-0002','device-selection-full-0001','device-selection-full-0002',
        'device-production-selection-0001','device-development-restore-0010','conflict-smoke-0007','relevance-smoke-0004','representation-smoke-0004','source-text-smoke-0002',
        'demo-apk-inspection-0011','selection-gate-0001','selection-gate-0002']
    blocked={'.private','__pycache__','build','.gradle','.cxx','.kotlin','temp','stage','host-temp','runner-temp'};outputs={}
    def capture(folder):
        for path in sorted(folder.iterdir()):
            if path.name in blocked or path.name.endswith('-temp'):continue
            assert path.resolve().is_relative_to(ROOT),path
            if path.is_dir():capture(path)
            elif path.suffix not in ('.apk','.pyc','.class') and path!=target:
                assert path.suffix.lower() not in ('.jks','.key','.keystore','.pem','.seed','.seed32'),'Private custody is excluded before reading'
                outputs[path.relative_to(ROOT).as_posix()]=file_sha(path)
    for name in names:
        folder=M4/name;assert folder.is_dir(),name;capture(folder)
    snapshots={}
    for name in ['PLAN.md','STATUS.md','DECISIONS.md','docs/v1.3/M4D3_METHODS.md','docs/v1.3/M4D3_SELECTION_FREEZE_AUDIT.md','docs/v1.3/M4_INCREMENT_PLAN.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md','docs/architecture-compliance-matrix.md','docs/v1.3/FINAL_DELIVERY_PLAN.md']:
        saved=HERE/'state-snapshot'/name;saved.parent.mkdir(parents=True,exist_ok=True);assert not saved.exists();saved.write_bytes((ROOT/name).read_bytes())
        snapshots[name]=file_sha(ROOT/name);outputs[saved.relative_to(ROOT).as_posix()]=file_sha(saved)
    record=dict(status='M4D3_SELECTION_FREEZING_VERIFIED_NOT_COMPLETE_M4_OR_PRODUCT',recorded_utc=datetime.now(timezone.utc).isoformat(),
        python_tests=1010,host_methods_per_variant=34,runtime_inputs=len(sources),android_inputs=len(android),historical_unchanged=len(history),
        prior_d2_gate_sha256=file_sha(M4/'representation-gate-0002/gate.json'),prior_d2_outputs_unchanged=len(prior['output_sha256']),
        original_model_format_failure_preserved=True,post_observation_format_control_not_heldout=True,phone=phone,
        source_sha256=sources,android_source_sha256=android,output_sha256=outputs,documents_at_closure=snapshots,
        limits=['Original plain safety question remains a supported-format failure with correct conservative rejection; no silent policy relaxation',
            'Four selected facts do not establish exhaustive safety coverage of the five-fact manual',
            'Synthetic controls are not owner final content, genuine review, release calibration, held-out accuracy or performance',
            'Mutation guards simulate trusted in-memory changes, not physical disk races/power loss',
            'Mobile data remains on; product APK has no INTERNET; no airplane isolation claim',
            'Demo is instrumentable and Android Debug signed; final nondebuggable release/UI/assets/software evaluation remain required',
            'Owner supplies final knowledge-pack content; its acceptance remains separate from agent software delivery'])
    target.write_text(json.dumps(record,indent=2)+'\n');print(record['status'])
if __name__=='__main__':main()
