"""Additional actual packaged MANAGE_DOCUMENTS test-provider isolation contract."""
import argparse,hashlib,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);args=parser.parse_args()
target=HERE/(args.build+'-picker-contracts.json');assert not target.exists()
capture=json.loads((HERE/(args.build+'-capture.json')).read_text());assert capture['status']=='PASS_F2_API_ITERATION_HOST_APK_CONTRACTS_NOT_DEVICE_OR_F2_ACCEPTANCE'
build=M4/args.build;commands=[];aapt=ROOT/'vendor/android-sdk/build-tools/37.0.0/aapt2.exe'
for name in ['app-debug.apk','app-debug-androidTest.apk']:
    argv=[str(aapt),'dump','xmltree',str(build/name),'--file','AndroidManifest.xml'];r=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',errors='replace',check=True,timeout=30)
    commands.append(dict(argv=argv,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
    if name=='app-debug.apk':assert 'AssetFixtureDocumentsProvider' not in r.stdout and 'android.permission.MANAGE_DOCUMENTS' not in r.stdout and 'android.permission.INTERNET' not in r.stdout
    else:assert 'AssetFixtureDocumentsProvider' in r.stdout and 'android.permission.MANAGE_DOCUMENTS' in r.stdout and 'android.content.action.DOCUMENTS_PROVIDER' in r.stdout
assert sha(build/'app-debug.apk')==sha(M4/'build-0067/app-debug.apk')
namespace='{http://schemas.android.com/apk/res/android}'
manifest=ET.parse(ROOT/'product/android/app/src/androidTest/AndroidManifest.xml').getroot()
provider=next(p for p in manifest.find('application').findall('provider') if p.get(namespace+'name')=='org.packrag.product.AssetFixtureDocumentsProvider')
assert provider.get(namespace+'permission')=='android.permission.MANAGE_DOCUMENTS' and provider.get(namespace+'exported')=='true' and provider.get(namespace+'grantUriPermissions')=='true'
record=dict(status='PASS_PACKAGED_TEST_ONLY_PROTECTED_DOCUMENT_PROVIDER_PRODUCT_UNCHANGED_NOT_PICKER_UI_ACCEPTANCE',host_capture_sha256=sha(HERE/(args.build+'-capture.json')),build=args.build,unchanged_product_0067_sha256=sha(build/'app-debug.apk'),commands=commands,
    scope='Actual APK manifest strings/source-bound exact provider attributes and product absence verified; product remains byte-identical to physically passing ViewModel0067. Test-only read-only selected-doc provider, no product MANAGE_DOCUMENTS/INTERNET privilege. Background denied-read and actual picker/grant/UI/native/visual tests still separate.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
