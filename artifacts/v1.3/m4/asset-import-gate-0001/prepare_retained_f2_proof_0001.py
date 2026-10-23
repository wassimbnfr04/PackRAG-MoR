"""Independently bind earlier selected F2 phone runs to final inputs; no new test claim."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=HERE.parent
target=HERE/'retained-f2-selected-identity-0001.json';assert not target.exists()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
current=read(M4/'build-0076/source-at-build-start.json')['files']
assert current==read(M4/'build-0077/source-at-build-start.json')['files'] and len(current)==599
pair=read(HERE/'adjacent-source-pair-0001.json');guards=set(pair['changed_guard_sources']);assert len(guards)==11
for name,value in current.items():assert sha(ROOT/name)==value,name
records=[]
for run,build,variant,class_name,controls in [
 ('device-local-asset-import-ui-0004','build-0073','debug','LocalAssetImportUiDeviceTest',8),
 ('device-local-asset-import-visual-0003','build-0075','debug','LocalAssetImportVisualDeviceTest',3),
 ('device-local-asset-import-all-slots-policy-0001','build-0070','demo','LocalAssetImportAllSlotsDeviceTest',8)]:
    directory=M4/run;manifest=read(directory/'instrumentation-manifest.json')
    assert manifest['status']=='PASS' and manifest['variant']==variant
    assert re.search(r'OK \(1 test\)',(directory/'instrumentation.txt').read_text())
    selected=manifest['selected_test_sources']['org.packrag.product.'+class_name]
    assert current[selected['source']]==selected['source_sha256']
    previous=read(M4/build/'source-at-build-start.json')['files']
    changes={name:dict(before=value,after=current.get(name)) for name,value in previous.items() if current.get(name)!=value}
    if class_name=='LocalAssetImportAllSlotsDeviceTest':
        # Picker-test repairs are unrelated to the all-slot test's provider/runtime dependencies.
        permitted=guards|{'product/android/app/src/androidTest/java/org/packrag/product/LocalAssetImportUiDeviceTest.kt'}
    else:permitted=guards
    assert set(changes)<=permitted,(run,changes)
    assert not previous.keys()-current.keys()
    additions={name:value for name,value in current.items() if name not in previous}
    if additions:assert set(additions)=={'product/android/app/src/androidTest/java/org/packrag/product/LocalAssetImportVisualDeviceTest.kt'}
    old_apk=M4/build/('app-'+variant+'.apk');new_apk=M4/('build-0076' if variant=='debug' else 'build-0077')/old_apk.name
    assert sha(old_apk)==sha(new_apk)==manifest['apk_sha256'][old_apk.name]
    collection=read(directory/'collected-results.json');assert collection['status']=='PASS'
    originals=collection['saved_sha256']
    main='m4-local-asset-import-'+('ui' if class_name=='LocalAssetImportUiDeviceTest' else 'visual' if class_name=='LocalAssetImportVisualDeviceTest' else 'all-slots')+'.json'
    value=read(directory/'original-adb'/main)
    assert value['status']=='PASS' and len(value['cases'])==controls and all(x['passed'] is True for x in value['cases'])
    for name,digest in originals.items():assert sha(directory/'original-adb'/name)==digest
    records.append(dict(run=run,original_build=build,variant=variant,methods=1,controls=controls,
        selected_class_sha256=selected['source_sha256'],product_apk_sha256=sha(new_apk),
        unchanged_prior_inputs=len(previous)-len(changes),changed_unselected_test_inputs=changes,added_unselected_test_inputs=additions,
        manifest_sha256=sha(directory/'instrumentation-manifest.json'),collection_sha256=sha(directory/'collected-results.json'),original_sha256=originals))
record=dict(status='PASS_RETAINED_F2_SELECTED_SOURCE_AND_WHOLE_PRODUCT_IDENTITY_NOT_FRESH_EXECUTION',
    recorded_utc=datetime.now(timezone.utc).isoformat(),final_android_inputs=599,runs=records,
    scope='Original run dates/builds and test APK hashes remain unchanged. Every prior input except explicitly listed unselected guard/picker-test repairs matches; added visual test is unselected for older runs. Selected tests, shared support/providers, fixtures, product code and whole product APK are identical. UI4 actual eight phone controls remain separately accepted; its original visual review remains FAIL, remedied only by separate visual3 three-control template experiment/independent visible-scope review. Approved all-slots uses signed calibration-schema-only synthetic fixture, not owner content, real gold or final release. Comprehensive fresh full regression remains mandatory at F4.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'],flush=True)
