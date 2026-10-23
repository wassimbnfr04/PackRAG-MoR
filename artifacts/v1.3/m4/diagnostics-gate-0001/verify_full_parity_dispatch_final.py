"""New E3 saved-result contracts against immutable accepted oracles; no gold regeneration."""
import hashlib,json,textwrap
from datetime import datetime,timezone
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(name,path):
    spec=spec_from_file_location(name,path);module=module_from_spec(spec);spec.loader.exec_module(module);return module
def originals(run):
    manifest=read(run/'instrumentation-manifest.json');saved=read(run/'collected-results.json')
    assert manifest['status']==saved['status']=='PASS' and manifest['apk_sha256']==saved['apk_sha256']
    for n,v in saved['saved_sha256'].items():assert sha(run/'original-adb'/n)==v and read(run/n)==read(run/'original-adb'/n)
    return saved
def verify():
    assert read(HERE/'full-background-execution.json')['status']=='PASS_E3_FULL_DEVELOPMENT_POLICY_RESTORATION_ORIGINALS_NOT_PARITY_OR_CLOSURE'
    gate=read(M4/'source-details-gate-0001/gate.json');prior=read(M4/'selection-gate-0002/gate.json')
    old=M4/'selection-gate-0002/retained_checks_reporting.py';assert sha(old)==prior['output_sha256'][old.relative_to(ROOT).as_posix()]
    env=dict(load('e3_retained_no_main',old).__dict__)
    a=read(M4/'build-0052/source-at-build-start.json')['files'];b=read(M4/'build-0053/source-at-build-start.json')['files'];assert a==b and len(a)==574
    for n,v in a.items():assert sha(ROOT/n)==v,n
    env['builds']={'build-0052':a,'build-0053':b}
    env['apk_hashes']={build:{p.name:sha(p) for p in (M4/build).glob('*.apk')} for build in env['builds']}
    env['PHONE']={}
    specs=[('device-diagnostics-full-0001','build-0052',37,'device-source-details-full-0001',
            ['org.packrag.product.DiagnosticRuntimeDeviceTest','org.packrag.product.DiagnosticLifecycleDeviceTest'],['m4-diagnostic-runtime.json','m4-diagnostic-lifecycle.json']),
        ('device-diagnostics-policy-full-0001','build-0053',30,'device-source-details-policy-full-0001',
            ['org.packrag.product.DiagnosticPolicyDeviceTest'],['m4-diagnostic-policy.json'])]
    for run,build,methods,reference,classes,extra in specs:
        files=extra+list(read(M4/reference/'collected-results.json')['saved_sha256']);saved=originals(M4/run)
        assert len(files)==len(set(files)) and set(files)==set(saved['saved_sha256'])
        manifest=read(M4/run/'instrumentation-manifest.json')
        assert manifest['class_name']==','.join(classes)+','+read(M4/reference/'instrumentation-manifest.json')['class_name']
        assert manifest['variant']==('debug' if build=='build-0052' else 'demo')
        env['PHONE'][run]=(build,methods,files)
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
    exec(compile(block,str(old)+'#unchanged-phone-contracts','exec'),env)
    selection=load('e3_selection_no_main',M4/'selection-gate-0002/verify_selection.py')
    selection_results={name:selection.verify(M4/name) for name in env['PHONE']}
    checker=M4/'source-details-gate-0001/verify_new_results.py';assert sha(checker)==gate['output_sha256'][checker.relative_to(ROOT).as_posix()]
    sources=load('e3_sources_no_main',checker);source_results={name:sources.phone(M4/name) for name in env['PHONE']}
    for actual,expected in [(False,0),(True,1),(1.0,1),(None,False),('1',1)]:
        try:sources.exact_typed(actual,expected)
        except AssertionError:pass
        else:raise AssertionError('Typed saved-source comparator accepted wrong JSON type')
    desktop=sources.desktop() # Explicit retained E2 executions under equal188 inputs, not labelled fresh.
    run=M4/'existing-walking-smoke-0016';walk=read(run/'smoke-results.json')
    assert walk['status']=='PASS' and len(walk['cases'])==14 and all(row['passed'] for row in walk['cases'])
    assert read(run/'inputs.json')['source_sha256']==gate['source_sha256']
    assert read(HERE/'desktop-walking-retry-execution.json')['status']=='PASS_NEW_ACTUAL_DESKTOP_WALKING_HOST_PERMISSION_RETRY_NOT_FULL_E3'
    development=M4/'device-diagnostics-full-0001';runtime=read(development/'m4-diagnostic-runtime.json');life=read(development/'m4-diagnostic-lifecycle.json')
    assert runtime['status']==life['status']=='PASS' and len(runtime['cases'])==8 and len(life['cases'])==7
    assert runtime['actual_weight_inference'] and life['actual_native_replacement_entry'] and life['actual_native_cancel_entry'] and life['actual_recovery_generation']
    policy=read(M4/'device-diagnostics-policy-full-0001/m4-diagnostic-policy.json')
    assert policy['status']=='PASS' and len(policy['cases'])==8 and policy['compiled_developer_mode'] is False and policy['build_type']=='demo' and policy['actual_weight_inference']
    for result in [runtime,policy]:
        assert all(row['passed'] for row in result['cases']) and result['raw_reasoning_persisted'] is False
        for phase in ['cold','warm']:
            row=result[phase];assert row['outcome']=='ANSWER_ACCEPTED' and '74 °C' in row['answer'] and '[S1]' in row['answer'] and '</think>' not in row['answer']
            assert 0<row['prefill_tokens']<=1536 and 0<row['evidence_tokens']<=1200 and 0<row['emitted_tokens_including_terminal']<=512
            reasoning=row['reasoning_through_closing_marker'];remaining=row['remaining_final_and_terminal']
            assert (reasoning is None and remaining is None) or (type(reasoning) is type(remaining) is int and reasoning>=0 and remaining>=0 and reasoning+remaining==row['emitted_tokens_including_terminal'])
        assert result['cold']['initialization_ms']>0 and result['warm']['initialization_ms']==0
    assert all(row['passed'] for row in life['cases']) and life['raw_reasoning_persisted'] is False
    restore=M4/'device-development-restore-0014';originals(restore)
    assert 'OK (1 test)' in (restore/'instrumentation.txt').read_text(encoding='utf-8')
    assert read(restore/'instrumentation-manifest.json')['apk_sha256']==env['apk_hashes']['build-0052']
    return dict(status='PASS_E3_FULL_RETAINED_AND_DIAGNOSTIC_PARITY_NOT_CLOSURE',recorded_utc=datetime.now(timezone.utc).isoformat(),
        phone=env['phone'],selection=selection_results,typed_signed_sources=source_results,typed_negative_controls=5,
        retained_desktop=desktop,fresh_desktop_walking_cases=14,retained_tokenizer_cases=43,retained_runtime_states=19,
        accepted_verifier_sha256=sha(old),exact_phone_contract_block_sha256=hashlib.sha256(block.encode('utf-8')).hexdigest(),
        limits='Immutable accepted expectations, not regenerated gold or exact model wording. Synthetic assertions/functional timing do not establish content authority, semantic entailment, genuine calibration or performance. Full E3 custody/history/state/closure still required.')
if __name__=='__main__':
    target=HERE/'full-parity.json';assert not target.exists();value=verify();target.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');print(value['status'])
