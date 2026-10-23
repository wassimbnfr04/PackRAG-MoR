"""Audit finished E2 short gates only; no foreground/full-suite acceptance claim."""
import hashlib,json,re
from datetime import datetime,timezone
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
target=HERE/'short-background-audit.json';assert not target.exists()
spec=spec_from_file_location('e2_source_parity_no_main',HERE/'verify_new_results.py');module=module_from_spec(spec);spec.loader.exec_module(module)
android=read(M4/'build-0039/source-at-build-start.json')['files'];assert android==read(M4/'build-0040/source-at-build-start.json')['files']
for name,value in android.items():assert sha(ROOT/name)==value,name
phone={}
for name,count,build,variant in [('device-source-details-0001',3,'build-0039','debug'),
    ('device-source-details-policy-0001',3,'build-0040','demo'),('device-development-restore-0014',1,'build-0039','debug')]:
    run=M4/name;manifest=read(run/'instrumentation-manifest.json');collection=read(run/'collected-results.json')
    assert manifest['status']==collection['status']=='PASS'
    apks={f'app-{variant}{suffix}.apk':sha(M4/build/f'app-{variant}{suffix}.apk') for suffix in ['', '-androidTest']}
    assert manifest['apk_sha256']==collection['apk_sha256']==apks and len(collection['saved_sha256'])==count
    for filename,value in collection['saved_sha256'].items():
        assert sha(run/'original-adb'/filename)==value and read(run/filename)==read(run/'original-adb'/filename)
        assert read(run/filename)['status']=='PASS'
    for item in manifest['selected_test_sources'].values():assert android[item['source']]==item['source_sha256']
    text=(run/'instrumentation.txt').read_text(encoding='utf-8');noun='test' if count==1 else 'tests'
    assert f'OK ({count} {noun})' in text and 'FAILURES' not in text
    match=re.search(r'Time:\s*([0-9][0-9\s\u00a0\u202f]*[.,][0-9]+)',text);assert match
    phone[name]=dict(methods=count,whole_instrumentation_seconds=float(re.sub(r'\s','',match[1]).replace(',','.')),
        original_results=count,apk_sha256=apks)
policy=read(M4/'device-source-details-policy-0001/m4-source-details-policy.json')
assert policy['compiled_developer_mode'] is False and len(policy['cases'])==2 and all(r['passed'] for r in policy['cases'])
viewmodel=read(M4/'device-source-details-0001/m4-source-details-viewmodel.json')
assert viewmodel['actual_weight_inference'] and len(viewmodel['cases'])==5 and all(r['passed'] for r in viewmodel['cases'])
assert (viewmodel['prefill_tokens'],viewmodel['evidence_tokens'])==(428,256) and 1<=viewmodel['emitted_tokens']<=512
assert viewmodel['raw_reasoning_persisted'] is False
assert viewmodel['owner_registry_and_model_sha256']==read(M4/'device-query-controls-0001/m4-ui-query-runtime.json')['owner_registry_and_model_sha256']
assert len(read(M4/'device-development-restore-0014/m3-import-consent.json')['cases'])==4
recovery=read(HERE/'restoration-recovery.json')
assert recovery['status']=='PASS_FRESH_DEVELOPMENT_RESTORATION_ORIGINAL_SAVED_PRIOR_COLLECTION_FAILURE_PRESERVED_NOT_E2_CLOSURE'
assert read(M4/'device-development-restore-0012/instrumentation-manifest.json')['status']=='FAIL'
for path,key in [(M4/'device-development-restore-0012/instrumentation-manifest.json','failed_manifest_sha256'),
    (M4/'device-development-restore-0012/instrumentation.txt','original_instrumentation_sha256'),
    (HERE/'restoration-0012-recovered-original.json','recovered_original_sha256')]:assert sha(path)==recovery[key]
assert read(HERE/'restoration-0012-recovered-original.json')==read(M4/'device-development-restore-0014/m3-import-consent.json')
record=dict(status='PASS_E2_SHORT_BACKGROUND_GATES_ORIGINALS_AND_RESTORATION_NOT_UI_FULL_SUITE_OR_CLOSURE',
    recorded_utc=datetime.now(timezone.utc).isoformat(),phone=phone,source_values={name:module.phone(M4/name) for name in phone if name!='device-development-restore-0014'},
    desktop=module.desktop(),saved_successful_originals=7,collection_failure_preserved=True,
    recovery_record_sha256=sha(HERE/'restoration-recovery.json'),android_inputs=len(android),
    owner_guard='New actual ViewModel before/after models and default registries match retained E1 guard',
    limits=['Explicit isolated fixture-reader keys are not app trust admission','Demo debug signed/instrumentable, not final product release',
        'No foreground UI, full retained phone-suite acceptance, benchmark, real content review or semantic entailment claim'])
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
