"""Fail-closed F2 closure. Requires actual originals, restoration and retained identities."""
import hashlib,json,re,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=HERE.parent
target=HERE/'gate.json';assert not target.exists()
BLOCKED={'.private','build','.gradle','.cxx','.kotlin','__pycache__','temp','stage','runner-temp','host-temp','pytest-temp'}
FORBIDDEN={'.apk','.pyc','.class','.seed','.seed32','.pem','.key','.keystore','.jks','.gguf','.onnx','.safetensors'}
def public(p):
    assert p.is_relative_to(ROOT) and not BLOCKED.intersection(x.lower() for x in p.relative_to(ROOT).parts)
    assert p.suffix.lower() not in FORBIDDEN,p
    for component in [p,*p.parents]:
        assert not component.is_symlink(),component
        if component==ROOT:break
    assert p.resolve().is_relative_to(ROOT),p
def read(p):public(p);return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    public(p)
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def mapping_check(files):
    for name,value in files.items():assert sha(ROOT/name)==value,name
def required(name,status):
    d=read(HERE/name);assert d['status']==status,(name,d['status']);return d
f1path=M4/'asset-readiness-gate-0001/gate.json';f1=read(f1path)
assert sha(f1path)=='8d2aa7f2e124db62c11330f43005b2b2f2cbfca818a2e0939b94dc3936c9cca7'
mapping_check(f1['output_sha256']);mapping_check(f1['source_sha256'])
history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];assert len(history)==587;mapping_check(history)
assert sha(ROOT/'FULL DOCUMENTATION.md')=='7c68e26003dc2debfbe4de9ce79467953fec5268c59947b93b2f2c01d612dbca'
assert sha(ROOT/'artifacts/v1.3/architecture/architecture-v1.3.docx')=='9b02f83b186a5b7f0101add861c6ecb40f5eb0b13016f50fa0c76efc6de07536'
pair=required('adjacent-source-pair-0001.json','PASS_MATCHED_599_HOST73_GUARD_ONLY_BUILDS_NOT_PHONE_ACCEPTANCE')
sources=read(M4/'build-0076/source-at-build-start.json')['files'];assert len(sources)==599
assert sources==read(M4/'build-0077/source-at-build-start.json')['files']==pair['android_source_sha256'];mapping_check(sources)
apk_pairs={}
for build,variant in [('build-0076','debug'),('build-0077','demo')]:
    capture=required(build+'-capture.json','PASS_F2_API_ITERATION_HOST_APK_CONTRACTS_NOT_DEVICE_OR_F2_ACCEPTANCE')
    assert capture['variant']==variant and capture['host_xml_totals']==dict(tests=73,failures=0,errors=0,skipped=0)
    assert 'android.permission.INTERNET' not in capture['commands'][0]['stdout']
    apk_pairs[variant]=capture['apk_sha256']
    # APKs are public separately bound binaries, deliberately excluded from source/evidence whitelist.
    for name,value in capture['apk_sha256'].items():
        p=M4/build/name;assert not p.is_symlink()
        with p.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==value
    with zipfile.ZipFile(M4/build/('app-'+variant+'.apk')) as archive:
        native=archive.read('lib/arm64-v8a/libpackrag_jni.so')
        assert len(native)==5597496 and hashlib.sha256(native).hexdigest()=='361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef'
def verify_run(row,variant,retained=False):
    run=M4/row['run'];manifest=read(run/'instrumentation-manifest.json')
    assert manifest['status']=='PASS' and manifest['variant']==variant
    if not retained:assert manifest['apk_sha256']==apk_pairs[variant]
    else:assert manifest['apk_sha256']['app-'+variant+'.apk']==apk_pairs[variant]['app-'+variant+'.apk']
    for source in manifest['selected_test_sources'].values():assert sources[source['source']]==source['source_sha256']
    text=(run/'instrumentation.txt').read_text();assert re.search(r'OK \('+str(row['methods'])+r' tests?\)',text) and 'FAILURES' not in text
    if 'manifest_sha256' in row:assert sha(run/'instrumentation-manifest.json')==row['manifest_sha256']
    for name,value in row['original_sha256'].items():
        assert sha(run/'original-adb'/name)==value
        d=read(run/'original-adb'/name);assert d['status']=='PASS' and all(case['passed'] is True for case in d['cases'])
    return dict(run=row['run'],variant=variant,methods=row['methods'],controls=row['controls'],manifest_sha256=sha(run/'instrumentation-manifest.json'),original_sha256=row['original_sha256'],retained_earlier_execution=retained)
accepted=[]
for variant,total in [('debug',(8,44)),('demo',(6,26))]:
    d=required('device-local-asset-adjacent-'+variant+'-0001-execution.json','PASS_F2_FRESH_ADJACENT_BACKGROUND_VARIANT_NOT_FULL_F2')
    assert (sum(x['methods'] for x in d['completed']),sum(x['controls'] for x in d['completed']))==total
    accepted.extend(verify_run(x,variant) for x in d['completed'])
core=required('device-local-asset-final-import-debug-0002-execution.json','PASS_FINAL_SOURCE_IMPORT_7_METHODS_54_CONTROLS_NOT_FULL_F2')
assert (sum(x['methods'] for x in core['completed']),sum(x['controls'] for x in core['completed']))==(7,54)
accepted.extend(verify_run(x,'debug') for x in core['completed'])
ui=required('adjacent-ui-visual-review-0001.json','PASS_F2_ADJACENT_UI_VISIBLE_SCOPE_NOT_FULL_F2');assert (ui['methods'],ui['controls'])==(6,31)
for selection,row in ui['class_proofs'].items():
    name='device-local-asset-adjacent-ui-0001-'+selection
    assert sha(HERE/(name+'-execution.json'))==row['execution_sha256']
    accepted.append(verify_run(dict(row,run=name),'debug'))
    for png,info in row['pngs'].items():assert sha(M4/name/'original-adb'/png)==info['sha256']
for selection,value in ui['visible_review_sha256'].items():
    p=HERE/('adjacent-ui-'+selection+'-visual-review-0001.json');assert sha(p)==value and read(p)['status'].startswith('PASS_')
retained=required('retained-f2-selected-identity-0001.json','PASS_RETAINED_F2_SELECTED_SOURCE_AND_WHOLE_PRODUCT_IDENTITY_NOT_FRESH_EXECUTION')
assert [(x['methods'],x['controls']) for x in retained['runs']]==[(1,8),(1,3),(1,8)]
accepted.extend(verify_run(x,x['variant'],True) for x in retained['runs'])
visual=required('visual-inspection-visual0003.json','PASS_VISUAL_SEPARATE_PICKER_TEMPLATE_SCOPE_NOT_FULL_F2')
for name,row in visual['reviews'].items():
    assert row['status']=='PASS_VISIBLE_SCOPE' and sha(M4/'device-local-asset-import-visual-0003/original-adb'/name)==row['sha256']
assert read(HERE/'visual-inspection-ui0004.json')['status'].startswith('FAIL')
assert read(HERE/'device-local-asset-final-import-debug-0001-execution.json')['status']=='FAIL_HOLD_LATER_IMPORTS_AND_F3'
restore=required('debug-restoration-and-final-guards-0001.json','PASS_F2_EXACT_DEBUG_RESTORATION_CONSENT4_OWNER50_SOURCE4_NOT_CLOSURE')
installed=required('adjacent-debug-restoration-0001.json','PASS_SERIAL_INSTALLED_EXACT_APK_PAIR_NO_TEST_ACCEPTANCE')
assert installed['apk_sha256']=={'org.packrag.product':apk_pairs['debug']['app-debug.apk'],'org.packrag.product.test':apk_pairs['debug']['app-debug-androidTest.apk']}
owner=required('owner-at-f2-closure-nofollow-0001.json','PASS_EXACT50_PUBLIC_OWNER_CLOSURE_NOFOLLOW_SNAPSHOT')
assert owner['owner_public_file_sha256']==read(HERE/'before.json')['owner_public_file_sha256']
source4=required('source4-at-f2-closure-0001.json','PASS_OWNED_FULL_ASSET_SOURCE_SET_VALIDATED_NOT_IMPORT_OR_F2_ACCEPTANCE');assert source4['source_total_bytes']==2009206667
consent=M4/'device-local-asset-final-debug-consent-0001';original=read(consent/'original-adb/m3-import-consent.json')
assert original['status']=='PASS' and len(original['cases'])==4 and all(x['passed'] is True for x in original['cases'])
assert sha(consent/'original-adb/m3-import-consent.json')==restore['original_sha256']
cleanup=required('interrupted-visual-root-cleanup-0001.json','PASS_EXACT_KNOWN_INTERRUPTED_TEST_ROOT_PUBLIC_BYTES_PRESERVED_AND_REMOVED_NOT_FULL_F2')
for row in cleanup['saved_public_originals'].values():assert sha(ROOT/row['path'])==row['sha256'] and (ROOT/row['path']).stat().st_size==row['bytes']
assert sum(x['bytes'] for x in cleanup['saved_public_originals'].values())==62787
# Exclude custody/weights/temp directories before traversal, hashing or manifest insertion.
outputs={}
def collect(directory):
    public(directory)
    for p in sorted(directory.iterdir()):
        if p.name.lower() in BLOCKED or p.suffix.lower() in FORBIDDEN:continue
        public(p)
        if p.is_dir():collect(p)
        elif p.is_file():outputs[p.relative_to(ROOT).as_posix()]=sha(p)
collect(HERE)
prefixes=('device-local-asset-import-','device-local-asset-final-','device-local-asset-adjacent-')
for p in sorted(M4.iterdir()):
    if p.name.startswith(prefixes) and p.is_dir():collect(p)
for number in range(58,78):
    directory=M4/('build-'+str(number).zfill(4))
    if directory.is_dir():collect(directory)
record=dict(status='M4F2_PINNED_PRIVATE_ASSET_IMPORT_ATOMICITY_CANCEL_RESTART_PICKER_AND_REGRESSIONS_VERIFIED_NOT_FULL_M4_OR_PRODUCT',
    recorded_utc=datetime.now(timezone.utc).isoformat(),prior_f1_gate_sha256=sha(f1path),historical_unchanged=587,
    retained_python_tests=1034,python_scope='Prior1034 tests retained with identical188 runtime inputs; no fresh execution at F2. F4 must run full fresh regression.',
    source_sha256=f1['source_sha256'],android_source_sha256=sources,apk_sha256=apk_pairs,accepted_runs=accepted,
    debug_final_import=dict(methods=7,controls=54),debug_adjacent=dict(methods=8,controls=44),approved_adjacent=dict(methods=6,controls=26),
    adjacent_foreground=dict(methods=6,controls=31),retained_picker=dict(methods=1,controls=8),retained_template_visual=dict(methods=1,controls=3),retained_approved_all_slots=dict(methods=1,controls=8),restored_consent=dict(methods=1,controls=4),
    owner50_sha256=owner['owner_public_file_sha256'],output_sha256=dict(sorted(outputs.items())),
    scope='F2 functional software acceptance only. Exact source/APK identities, original JUnit/reports and separate bounded manual visible reviews; every historical failure unchanged. First narrow callback failure root cause/permanent repair unproved; strict unchanged retry passes, F4 must persist exact callback text before assertions. UI4 original visual FAIL unchanged; separate visual3 remedies template viewport only. AR/FR viewer component controls not new production inference; encoder raster status only. Import subprocess SIGKILL not power loss. Cooperative provider cancellation not arbitrary provider timing. Owner custody only explicit50 public paths; historical F1 default-registry change is not undone. Mobile data remains on/no INTERNET permission, not radio isolation. Thermal/resource snapshots observational near uncertain completion phase, not controlled performance or causal bottleneck proof. Approved fixtures are software calibration-schema tests, not owner content/human gold/final nondebug signed release. Readonly source4 retained; known interrupted root public bytes preserved then bounded cleanup. F3/F4, later scoped tooling/evaluation/release/delivery remain; exact F2 Git checkpoint required before F3.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'],len(outputs),flush=True)
