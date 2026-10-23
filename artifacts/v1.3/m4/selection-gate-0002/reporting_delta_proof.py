"""Bounded reuse: one test JSON-key rename, identical product APK bytes."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def prove(require_device=True):
    repair=read(HERE/'timing-reporter-repair.json');path=repair['source']
    before=(HERE/'timing-reporter-before.kt').read_bytes();after=(ROOT/path).read_bytes()
    assert digest(HERE/'timing-reporter-before.kt')==repair['old_source_sha256']
    assert digest(ROOT/path)==repair['new_source_sha256']
    assert before.count(repair['old_field'].encode())==1
    assert after==before.replace(repair['old_field'].encode(),repair['new_field'].encode())
    builds={name:read(M4/name/'source-at-build-start.json')['files'] for name in ['build-0028','build-0029','build-0030','build-0031']}
    assert builds['build-0028']==builds['build-0029'] and builds['build-0030']==builds['build-0031']
    old=builds['build-0028'];new=builds['build-0030'];assert set(old)==set(new) and len(new)==543
    assert [k for k in old if old[k]!=new[k]]==[path]
    assert old[path]==repair['old_source_sha256'] and new[path]==repair['new_source_sha256']
    for k,v in new.items():assert digest(ROOT/k)==v,k
    apk={}
    for previous,current,variant in [('build-0028','build-0030','debug'),('build-0029','build-0031','demo')]:
        assert read(M4/current/'build-result.json')['exit_code']==0
        assert read(M4/current/'host-test-summary.json')['test_methods']==34
        filename=f'app-{variant}.apk';assert digest(M4/previous/filename)==digest(M4/current/filename)
        apk[variant]=digest(M4/current/filename)
    retained=read(HERE/'development-retained-parity.json')
    assert retained['status']=='PASS_FULL_DEVELOPMENT_NOT_POLICY_RESTORATION_OR_D3_CLOSURE'
    manifest=read(M4/'device-selection-full-0002/instrumentation-manifest.json')
    assert manifest['status']=='PASS' and 'OK (30 tests)' in (M4/'device-selection-full-0002/instrumentation.txt').read_text()
    assert len(read(M4/'device-selection-full-0002/collected-results.json')['saved_sha256'])==30
    unchanged={}
    for name,selected in manifest['selected_test_sources'].items():
        p=selected['source'];assert old[p]==selected['source_sha256']
        if p!=path:assert old[p]==new[p];unchanged[name]=selected
    focused=None
    if require_device:
        run=M4/'device-selection-reporter-0001';focused=read(run/'instrumentation-manifest.json')
        assert focused['status']=='PASS' and focused['class_name']=='org.packrag.product.SelectionDeviceTest'
        assert 'OK (3 tests)' in (run/'instrumentation.txt').read_text()
        assert focused['apk_sha256']=={p.name:digest(p) for p in (M4/'build-0030').glob('*.apk')}
        assert all(s['source_sha256']==new[s['source']] for s in focused['selected_test_sources'].values())
        collection=read(run/'collected-results.json');assert collection['status']=='PASS' and len(collection['saved_sha256'])==3
        for name,value in collection['saved_sha256'].items():
            assert digest(run/'original-adb'/name)==value and read(run/name)==read(run/'original-adb'/name)
        rows=read(run/'m4-selection-runtime.json')['cases'];assert len(rows)==8
        assert all(repair['new_field'] in row and repair['old_field'] not in row for row in rows)
        assert read(HERE/'reporter-selection-parity.json')['status']=='PASS_D3_SELECTION_PARITY_NOT_COMPLETE_MILESTONE'
    return dict(status='PASS_BOUNDED_REPORT_ONLY_REUSE' if require_device else 'PASS_SOURCE_AND_PRODUCT_APK_IDENTITY_NOT_DEVICE_ACCEPTANCE',
        source_delta=repair,product_apk_sha256=apk,retained_full_development='device-selection-full-0002',
        unchanged_test_sources=unchanged,affected_three_method_run='device-selection-reporter-0001' if require_device else None,
        new_android_source_sha256=new,proof_sha256=digest(Path(__file__)),
        scope='Retain original full30 results under their original APK/test sources. Only one reporting key changed; rerun affected3. New full25 policy and restoration still required.')
if __name__=='__main__':
    import sys
    record=prove('--build-only' not in sys.argv);target=HERE/('reporter-build-identity.json' if '--build-only' in sys.argv else 'reporter-bounded-reuse.json')
    assert not target.exists();target.write_text(json.dumps(record,indent=2)+'\n');print(record['status'])
