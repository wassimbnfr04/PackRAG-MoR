"""Hash-exact missing-import recovery; not a saved-at-start source copy."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];M4=ROOT/'artifacts/v1.3/m4'
run=M4/'build-0017/source-recovery';run.mkdir(exist_ok=False)
record=json.loads((M4/'build-0017/source-at-build-start.json').read_text())
name='product/android/app/src/androidTest/java/org/packrag/product/RepresentationDeviceTest.kt'
current=(ROOT/name).read_bytes();needle=b'import org.packrag.retrieval.Retrieval\n';assert current.count(needle)==1
recovered=current.replace(needle,b'');assert hashlib.sha256(recovered).hexdigest()==record['files'][name]
(run/'RepresentationDeviceTest.kt').write_bytes(recovered)
(run/'recovery.json').write_text(json.dumps(dict(status='PASS_HASH_EXACT_SINGLE_IMPORT_RECONSTRUCTION_NOT_ORIGINAL_BUILD_START_COPY',
    original_build='build-0017',source=name,reconstructed_sha256=record['files'][name],current_sha256=hashlib.sha256(current).hexdigest(),
    operation='Remove the sole added Retrieval import newline; SHA256 must equal immutable failed build-start identity'),indent=2)+'\n')
print('Hash-exact failed build harness reconstruction PASS')
