"""E2 retained phone comparisons against immutable accepted D3 expectations."""
import hashlib,json,textwrap
from datetime import datetime,timezone
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(name,path):
    spec=spec_from_file_location(name,path);module=module_from_spec(spec);spec.loader.exec_module(module);return module
def verify():
    assert read(HERE/'full-device-execution.json')['status']=='PASS_ALL_DEVELOPMENT_POLICY_AND_RESTORATION_ORIGINALS_NOT_E2_CLOSURE'
    old=M4/'selection-gate-0002/retained_checks_reporting.py';gate=read(M4/'selection-gate-0002/gate.json')
    assert digest(old)==gate['output_sha256'][old.relative_to(ROOT).as_posix()]
    env=dict(load('retained_d3_no_main_e2',old).__dict__)
    a=read(M4/'build-0039/source-at-build-start.json')['files'];b=read(M4/'build-0040/source-at-build-start.json')['files'];assert a==b
    for name,value in a.items():assert digest(ROOT/name)==value,name
    env['builds']={'build-0039':a,'build-0040':b}
    env['apk_hashes']={build:{p.name:digest(p) for p in (M4/build).glob('*.apk')} for build in env['builds']}
    env['PHONE']={
        'device-source-details-full-0001':('build-0039',35,['m4-source-details-rows.json','m4-source-details-rejections.json','m4-source-details-viewmodel.json','m4-ui-query-runtime.json','m4-ui-query-inputs.json']+list(read(M4/'device-query-regression-0001/collected-results.json')['saved_sha256'])),
        'device-source-details-policy-full-0001':('build-0040',29,['m4-source-details-rows.json','m4-source-details-rejections.json','m4-source-details-policy.json']+list(read(M4/'device-query-policy-0001/collected-results.json')['saved_sha256']))}
    # Frozen accepted expectations remain unchanged; new desktop gates independently
    # verify the current 188-input runtime. No model wording is used as exact gold.
    env['token_cases']=read(M4/'conflict-smoke-0007/tokenizer-cases.json')
    env['conflict_desktop']=read(M4/'conflict-smoke-0007/conflict-smoke-results.json')
    env['relevant_token_oracle']={r['id']:r for r in read(M4/'relevance-smoke-0004/tokenizer-cases.json')['cases']}
    env['relevant_runtime_oracle']={r['id']:r for r in read(M4/'relevance-smoke-0004/relevance-smoke-results.json')['cases']}
    env['rep']=read(M4/'representation-fixtures-0001/cases.json')
    env['rep_token_oracle']={r['id']:r for r in read(M4/'representation-smoke-0004/tokenizer-cases.json')['cases']}
    env['rep_runtime_oracle']={r['id']:r for r in read(M4/'representation-smoke-0004/representation-smoke-results.json')['cases']}
    env['presence']=read(M4/'source-text-fixtures-0001/cases.json')
    env['presence_token_oracle']={r['id']:r for r in read(M4/'source-text-smoke-0002/source-text-smoke-results.json')['tokenizer_cases']}
    source=old.read_text(encoding='utf-8');assert source.count('    phone = {}\n')==source.count('    inspection=')==1
    block=textwrap.dedent('    phone = {}\n'+source.split('    phone = {}\n',1)[1].split('    inspection=',1)[0])
    for run_name,(build,methods,names) in env['PHONE'].items():
        manifest=read(M4/run_name/'instrumentation-manifest.json');collection=read(M4/run_name/'collected-results.json')
        assert len(names)==len(set(names)) and set(collection['saved_sha256'])==set(names)
        reference='device-query-regression-0001' if methods==35 else 'device-query-policy-0001'
        prefix='org.packrag.product.SourceDetailsDeviceTest,org.packrag.product.SourceDetailsViewModelTest,org.packrag.product.QueryControlsDeviceTest,' if methods==35 else 'org.packrag.product.SourceDetailsDeviceTest,org.packrag.product.SourceDetailsPolicyTest,'
        assert manifest['class_name']==prefix+read(M4/reference/'instrumentation-manifest.json')['class_name']
        for name,value in collection['saved_sha256'].items():
            assert digest(M4/run_name/'original-adb'/name)==value and read(M4/run_name/name)==read(M4/run_name/'original-adb'/name)
    exec(compile(block,str(old)+'#exact-phone-block','exec'),env)
    selection=load('retained_selection_no_main_e2',M4/'selection-gate-0002/verify_selection.py')
    selection_results={name:selection.verify(M4/name) for name in env['PHONE']}
    source_results=load('new_source_no_main_e2',HERE/'verify_new_results.py')
    return dict(status='PASS_E2_ALL_RETAINED_EXACT_PHONE_TOKEN_ADMISSION_RUNTIME_AND_NEW_SIGNED_SOURCE_PARITY_NOT_CLOSURE',
        recorded_utc=datetime.now(timezone.utc).isoformat(),accepted_verifier_sha256=digest(old),
        exact_phone_block_sha256=hashlib.sha256(block.encode('utf-8')).hexdigest(),phone=env['phone'],selection=selection_results,
        source_values={name:source_results.phone(M4/name) for name in env['PHONE']},desktop=source_results.desktop(),
        retained_actual_tokenizer_cases=43,retained_runtime_states=19,
        oracle_scope='Immutable accepted D3 expectations; current desktop gates separate; no regenerated gold or wording byte equality')
if __name__=='__main__':
    target=HERE/'retained-parity.json';assert not target.exists();value=verify()
    target.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');print(value['status'])
