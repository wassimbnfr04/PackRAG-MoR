"""New versioned runner: same APKs/test; explicitly choose ADB non-streaming install."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]; HERE=Path(__file__).parent
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
failure=HERE/'device-local-asset-import-visual-0001-execution.json'
assert json.loads(failure.read_text())['status']=='FAIL'
error=HERE/'device-local-asset-import-visual-0001-stage-0.stderr.txt'
assert 'subprocess.TimeoutExpired' in error.read_text() and "'install', '-r'" in error.read_text()
test_source=ROOT/'scripts/v13_test_android.py'; text=test_source.read_text()
text=text.replace('from product.packrag.config import file_sha', 'import sys\nsys.path.insert(0,str(Path(__file__).resolve().parents[4]))\nfrom product.packrag.config import file_sha',1)
assert 'ROOT = Path(__file__).resolve().parents[1]' in text
text=text.replace('ROOT = Path(__file__).resolve().parents[1]', 'ROOT = Path(__file__).resolve().parents[4]',1)
old='"install", "-r", str(path)'; assert text.count(old)==1
text=text.replace(old,'"install", "--no-streaming", "-r", str(path)',1)
test_runner=HERE/'test_android_nonstreaming_0001.py';assert not test_runner.exists();test_runner.write_text(text,encoding='utf-8')
visual_source=HERE/'run_visual.py';text=visual_source.read_text()
old="[sys.executable,'-X','utf8','-m','scripts.v13_test_android',";assert text.count(old)==1
text=text.replace(old,"[sys.executable,'-X','utf8',str(HERE/'test_android_nonstreaming_0001.py'),",1)
visual_runner=HERE/'run_visual_nonstreaming_0001.py';assert not visual_runner.exists();visual_runner.write_text(text,encoding='utf-8')
import ast
ast.parse(test_runner.read_text());ast.parse(visual_runner.read_text())
target=HERE/'visual-install-retry-preparation-0001.json';assert not target.exists()
target.write_text(json.dumps(dict(status='PREPARED_NOT_PHONE_ACCEPTED',failure_sha256=sha(failure),error_sha256=sha(error),original_runner_sha256=sha(test_source),new_test_runner_sha256=sha(test_runner),new_visual_runner_sha256=sha(visual_runner),scope='Initial visual0001 never entered instrumentation: product install-r transport timed out after180s. Preserve all failed originals/error-text captures; no test assertion/product failure inferred. New copied runner changes ROOT/sys.path solely for relocation and install command to --no-streaming -r; identical selected APKs/class/assertions. No uninstall/clear/radio/global setting change.'),indent=2)+'\n',encoding='utf-8')
print('PREPARED_NONSTREAMING_IDENTICAL_TEST_APKS')
