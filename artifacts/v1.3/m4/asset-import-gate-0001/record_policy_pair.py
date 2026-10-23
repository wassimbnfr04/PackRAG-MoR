"""Compare frozen debug/demo inputs and public APK contracts; no new phone acceptance."""
import hashlib,json,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
target=HERE/'picker-policy-source-pair-0001.json';assert not target.exists()
frozen={name:read(M4/name/'source-at-build-start.json')['files'] for name in ['build-0069','build-0070']}
assert frozen['build-0069']==frozen['build-0070'] and len(frozen['build-0069'])==598
for name,value in frozen['build-0069'].items():assert sha(ROOT/name)==value,name
contracts={};members={}
for build,variant in [('build-0069','debug'),('build-0070','demo')]:
    capture=read(HERE/(build+'-capture.json'));assert capture['variant']==variant and capture['host_xml_totals']==dict(tests=73,failures=0,errors=0,skipped=0)
    assert capture['status']=='PASS_F2_API_ITERATION_HOST_APK_CONTRACTS_NOT_DEVICE_OR_F2_ACCEPTANCE'
    apk=M4/build/f'app-{variant}.apk';assert sha(apk)==capture['apk_sha256'][apk.name]
    with zipfile.ZipFile(apk) as z:
        assert z.testzip() is None
        members[variant]={name:hashlib.sha256(z.read(name)).hexdigest() for name in ['lib/arm64-v8a/libpackrag_jni.so','assets/release-trust.json']}
    contracts[build]=dict(capture_sha256=sha(HERE/(build+'-capture.json')),apk_sha256=sha(apk),variant=variant)
assert members['debug']==members['demo']
result=dict(status='PASS_FROZEN_598_SOURCE_HOST_73_POLICY_PAIR_NOT_PHONE_OR_F2_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),runner_sha256=sha(Path(__file__)),android_source_sha256=frozen['build-0069'],builds=contracts,unchanged_public_native_and_trust=members,
    scope='Exact selected598 Android source identities and73 host XML methods per variant; actual Gradle logs distinguish executed/UP-TO-DATE tests. Packaged native and public trust bytes identical. APK policy variants differ; debug/demo instrumentable artifacts are not final signed nondebug release. Physical approved-policy and system picker/UI remain independent.')
target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'])
