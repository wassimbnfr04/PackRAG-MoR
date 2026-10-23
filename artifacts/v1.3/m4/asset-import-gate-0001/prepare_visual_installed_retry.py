"""Freeze a verified-installed retry, preserving original runners and failures."""
import ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
state=HERE/'visual-installed-state-0001.json';assert json.loads(state.read_text())['status']=='PASS_EXACT_INSTALLED_APK_IDENTITIES_NOT_VISUAL_ACCEPTANCE'
source=HERE/'test_android_nonstreaming_0001.py';text=source.read_text()
start=text.index('        for path in apks:')
end=text.index('        command = [str(ADB), "-s", args.serial, "shell", "am", "instrument"',start)
replacement='''        # Read only already-installed public APK paths; never race a pending reinstall.
        record["transport"]="VERIFY_EXACT_INSTALLED_APKS_NO_REINSTALL"
        packages=["org.packrag.product","org.packrag.product.test"]
        for package,path in zip(packages,apks):
            command=[str(ADB),"-s",args.serial,"shell","pm","path",package]
            result=subprocess.run(command,capture_output=True,text=True,encoding="utf-8",timeout=30)
            record["commands"].append(dict(argv=command,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
            value=result.stdout.strip()
            assert result.returncode==0 and re.fullmatch(r"package:/data/app/[A-Za-z0-9_./=+~-]+/base\\.apk",value),"Expected one installed public APK"
            installed_path=value.removeprefix("package:")
            command=[str(ADB),"-s",args.serial,"shell","sha256sum",installed_path]
            result=subprocess.run(command,capture_output=True,text=True,encoding="utf-8",timeout=30)
            record["commands"].append(dict(argv=command,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
            assert result.returncode==0 and result.stdout.split()[0]==file_sha(path),"Installed APK mismatch; stop without reinstall"
'''
text=text[:start]+replacement+text[end:]
test_runner=HERE/'test_android_installed_0001.py';assert not test_runner.exists();ast.parse(text);test_runner.write_text(text,encoding='utf-8')
visual_source=HERE/'run_visual_nonstreaming_0001.py';text=visual_source.read_text()
assert text.count("test_android_nonstreaming_0001.py")==1
text=text.replace("test_android_nonstreaming_0001.py","test_android_installed_0001.py",1)
visual_runner=HERE/'run_visual_installed_0001.py';assert not visual_runner.exists();ast.parse(text);visual_runner.write_text(text,encoding='utf-8')
target=HERE/'visual-installed-retry-preparation-0001.json';assert not target.exists()
target.write_text(json.dumps(dict(status='PREPARED_NOT_PHONE_ACCEPTED',installed_state_sha256=sha(state),old_runner_sha256=sha(source),new_test_runner_sha256=sha(test_runner),new_visual_runner_sha256=sha(visual_runner),scope='New versioned attempt verifies actual installed product/test APKs byte-for-byte against selected build before instrumentation, without install/uninstall/clear. Same class/APK/assertions/frozen599 sources. Earlier visual0001 install timeout and visual0002 PACKAGE UPDATED process interruption retained. Unknown actor/installer session identity and upload decision are not inferred from dismissed dialog.'),indent=2)+'\n',encoding='utf-8')
print('PREPARED_VERIFIED_INSTALLED_NO_REINSTALL_RETRY')
