"""Install only mismatched public APKs, serially; never start tests after unknown timeout."""
import argparse,hashlib,json,re,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;ADB=ROOT/'vendor/platform-tools/adb.exe'
parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);parser.add_argument('--variant',choices=['debug','demo'],required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
target=HERE/args.output;assert target.parent==HERE and not target.exists()
build=ROOT/'artifacts/v1.3/m4'/args.build;assert build.parent==ROOT/'artifacts/v1.3/m4'
capture=json.loads((HERE/(args.build+'-capture.json')).read_text());assert capture['variant']==args.variant and capture['status']=='PASS_LOCAL_F3F4_BUILD_HOST_APK_CONTRACTS_NOT_DEVICE_OR_INCREMENT_ACCEPTANCE'
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
record=dict(status='RUNNING_SERIAL_INSTALL_NO_TEST_STARTED',started_utc=datetime.now(timezone.utc).isoformat(),build=args.build,variant=args.variant,commands=[])
def adb(*argv,timeout=30):
    command=[str(ADB),'-s','R3CT908DHHR',*argv]
    result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    record['commands'].append(dict(argv=command,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
    target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,(command,result.stdout,result.stderr)
    return result.stdout
def installed(package):
    path=adb('shell','pm','path',package).strip()
    assert re.fullmatch(r'package:/data/app/[A-Za-z0-9_./=+~-]+/base\.apk',path),path
    value=adb('shell','sha256sum',path.removeprefix('package:')).split()[0]
    assert re.fullmatch('[0-9a-f]{64}',value)
    return value
try:
    expected={}
    for package,name in [('org.packrag.product','app-'+args.variant+'.apk'),('org.packrag.product.test','app-'+args.variant+'-androidTest.apk')]:
        path=build/name;value=sha(path);assert value==capture['apk_sha256'][name];expected[package]=value
        if installed(package)==value:
            print('REUSE_EXACT_INSTALLED',package,flush=True)
        else:
            print('SERIAL_INSTALL_START',package,flush=True)
            output=adb('install','--no-streaming','-r',str(path),timeout=180);assert 'Success' in output
            assert installed(package)==value
            print('SERIAL_INSTALL_VERIFIED',package,flush=True)
    # Check both identities after all mutations have completed, before permitting instrumentation.
    for _ in range(3):
        assert {package:installed(package) for package in expected}==expected
        time.sleep(0.5)
    record.update(status='PASS_SERIAL_INSTALLED_EXACT_APK_PAIR_NO_TEST_ACCEPTANCE',apk_sha256=expected,
        scope='Only mismatched public APKs replaced in place serially; unchanged product reused. All install commands terminalSuccess and actual installed hashes exact before any test. Three consecutive pair identity checks are observations, not proof against an unknown future installer. No uninstall/clear/radio/security setting/upload. Timeout means unknown installer outcome: do not run tests or start another install until device decision/session settled and exact hashes reverified.')
except subprocess.TimeoutExpired as failure:
    record.update(status='UNKNOWN_INSTALL_OUTCOME_HOLD_ALL_TESTS_AND_INSTALL_RETRIES',failure_type=type(failure).__name__,command=failure.cmd,timeout=failure.timeout)
    raise
except Exception as failure:
    record.update(status='FAIL_NO_TEST_STARTED',failure_type=type(failure).__name__,failure_message=str(failure));raise
finally:
    record['finished_utc']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(record['status'],flush=True)
