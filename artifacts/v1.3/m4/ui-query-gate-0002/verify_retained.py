"""Reapply the exact accepted D3 phone parity block to fresh E1 phone outputs."""
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
def verify(runs=None):
    old=M4/'selection-gate-0002/retained_checks_reporting.py';gate=read(M4/'selection-gate-0002/gate.json')
    assert digest(old)==gate['output_sha256'][old.relative_to(ROOT).as_posix()]
    module=load('retained_d3_no_main',old);env=dict(module.__dict__)
    a=read(M4/'build-0035/source-at-build-start.json')['files'];b=read(M4/'build-0036/source-at-build-start.json')['files'];assert a==b
    for name,value in a.items():assert digest(ROOT/name)==value,name
    env['builds']={'build-0035':a,'build-0036':b}
    env['apk_hashes']={build:{p.name:digest(p) for p in (M4/build).glob('*.apk')} for build in env['builds']}
    env['PHONE']={
        'device-query-regression-0001':('build-0035',30,list(read(M4/'device-selection-full-0002/collected-results.json')['saved_sha256'])),
        'device-query-policy-0001':('build-0036',26,['m4-ui-query-policy.json']+list(read(M4/'device-production-selection-0001/collected-results.json')['saved_sha256']))
    }
    if runs is not None:
        assert set(runs) and set(runs).issubset(env['PHONE'])
        env['PHONE']={name:value for name,value in env['PHONE'].items() if name in runs}
    env['token_cases']=read(M4/'conflict-smoke-0007/tokenizer-cases.json')
    env['conflict_desktop']=read(M4/'conflict-smoke-0007/conflict-smoke-results.json')
    relevant=read(M4/'relevance-smoke-0004/relevance-smoke-results.json')
    env['relevant_token_oracle']={r['id']:r for r in read(M4/'relevance-smoke-0004/tokenizer-cases.json')['cases']}
    env['relevant_runtime_oracle']={r['id']:r for r in relevant['cases']}
    env['rep']=read(M4/'representation-fixtures-0001/cases.json')
    env['rep_token_oracle']={r['id']:r for r in read(M4/'representation-smoke-0004/tokenizer-cases.json')['cases']}
    env['rep_runtime_oracle']={r['id']:r for r in read(M4/'representation-smoke-0004/representation-smoke-results.json')['cases']}
    env['presence']=read(M4/'source-text-fixtures-0001/cases.json')
    env['presence_token_oracle']={r['id']:r for r in read(M4/'source-text-smoke-0002/source-text-smoke-results.json')['tokenizer_cases']}
    source=old.read_text(encoding='utf-8')
    assert source.count('    phone = {}\n')==source.count('    inspection=')==1
    block=textwrap.dedent('    phone = {}\n'+source.split('    phone = {}\n',1)[1].split('    inspection=',1)[0])
    # The comparison block is byte-derived from an already accepted public verifier;
    # only the environment's explicit new run/build bindings differ. No oracle is regenerated.
    for run_name,(build,methods,names) in env['PHONE'].items():
        manifest=read(M4/run_name/'instrumentation-manifest.json');collection=read(M4/run_name/'collected-results.json')
        assert set(collection['saved_sha256'])==set(names)
        reference='device-selection-full-0002' if methods==30 else 'device-production-selection-0001'
        expected=read(M4/reference/'instrumentation-manifest.json')['class_name']
        if methods==26:expected='org.packrag.product.QueryControlsPolicyTest,'+expected
        assert manifest['class_name']==expected
        for name,value in collection['saved_sha256'].items():
            assert digest(M4/run_name/'original-adb'/name)==value
            assert read(M4/run_name/name)==read(M4/run_name/'original-adb'/name)
    exec(compile(block,str(old)+'#exact-phone-block','exec'),env)
    selection=load('retained_selection_no_main',M4/'selection-gate-0002/verify_selection.py')
    result={name:selection.verify(M4/name) for name in env['PHONE']}
    return dict(status='PASS_RETAINED_PHONE_ORIGINALS_EXACT_TOKEN_ADMISSION_RUNTIME_PROVENANCE_NOT_E1_CLOSURE',
        recorded_utc=datetime.now(timezone.utc).isoformat(),accepted_verifier=old.relative_to(ROOT).as_posix(),accepted_verifier_sha256=digest(old),
        exact_phone_block_sha256=hashlib.sha256(block.encode('utf-8')).hexdigest(),phone=env['phone'],selection=result,
        retained_actual_tokenizer_cases=43,retained_runtime_states=19,
        oracle_scope='Existing accepted D3 exact fixture comparisons reused as expectations, not new held-out gold or natural-language byte equality')
if __name__=='__main__':
    import sys
    development='--development-only' in sys.argv
    target=HERE/('development-parity.json' if development else 'retained-parity.json')
    assert not target.exists();value=verify(['device-query-regression-0001'] if development else None)
    target.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');print(value['status'])
