"""Matched fresh guard-regression builds and bounded retained-input proof."""
import hashlib,json,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'adjacent-source-pair-0001.json';assert not target.exists()
sources=read(M4/'build-0076/source-at-build-start.json')['files']
assert sources==read(M4/'build-0077/source-at-build-start.json')['files'] and len(sources)==599
old=read(M4/'build-0075/source-at-build-start.json')['files'];applied=read(HERE/'adjacent-guard-applied-0001.json')['files']
changed={name:value for name,value in sources.items() if old.get(name)!=value}
assert set(changed)==set(applied) and len(changed)==11 and set(sources)==set(old)
for name,value in sources.items():assert sha(ROOT/name)==value
for name,value in changed.items():assert value==applied[name]['proposed_sha256']
builds={};public={}
for build,variant,reference in [('build-0076','debug','build-0075'),('build-0077','demo','build-0070')]:
    capture=read(HERE/(build+'-capture.json'))
    assert capture['status']=='PASS_F2_API_ITERATION_HOST_APK_CONTRACTS_NOT_DEVICE_OR_F2_ACCEPTANCE'
    assert capture['variant']==variant and capture['host_xml_totals']==dict(tests=73,failures=0,errors=0,skipped=0)
    apk=M4/build/('app-'+variant+'.apk');assert sha(apk)==sha(M4/reference/apk.name)==capture['apk_sha256'][apk.name]
    with zipfile.ZipFile(apk) as archive:
        public[variant]={name:hashlib.sha256(archive.read(name)).hexdigest() for name in ['lib/arm64-v8a/libpackrag_jni.so','assets/release-trust.json']}
    builds[build]=dict(variant=variant,product_apk_sha256=sha(apk),byte_identical_reference=reference,capture_sha256=sha(HERE/(build+'-capture.json')))
assert public['debug']==public['demo']
target.write_text(json.dumps(dict(status='PASS_MATCHED_599_HOST73_GUARD_ONLY_BUILDS_NOT_PHONE_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),android_source_sha256=sources,changed_guard_sources=changed,builds=builds,shared_public_native_trust=public,scope='Fresh debug0076/demo0077 same599 inputs; exactly11 guard-only test sources differ from0075,588 inputs unchanged. Whole product APKs byte-identical to respective physically exercised debug0075/demo0070. Selected import/fault/process/all-slot/ViewModel/picker/visual sources, providers/support and runtime inputs unchanged, but instrumentation APKs are newly compiled with changed guard classes; prior physical results remain dated retained evidence, not new executions. Relevant adjacent physical regressions still required.'),indent=2)+'\n',encoding='utf-8')
print('PASS_MATCHED_599_HOST73_GUARD_ONLY_BUILDS_NOT_PHONE_ACCEPTANCE')
